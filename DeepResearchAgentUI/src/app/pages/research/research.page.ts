import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { catchError, forkJoin, map, of } from 'rxjs';

import { ResearchResponse } from '../../interfaces/research.interfaces';
import { SessionSummary, SessionTurn } from '../../interfaces/session.interfaces';
import { ResearchApiService } from '../../services/research-api.service';

interface UiSession extends SessionSummary {
  label: string;
}

interface ChatMessage {
  role: 'user' | 'assistant' | 'error';
  text: string;
  response?: ResearchResponse;
}

@Component({
  selector: 'app-research-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './research.page.html',
  styleUrl: './research.page.css',
})
export class ResearchPage implements OnInit {
  private readonly api = inject(ResearchApiService);

  readonly query = signal('');
  readonly location = signal('');
  readonly soilType = signal('');
  readonly currentSessionId = signal('');

  readonly showMeta = signal(true);
  readonly apiConnected = signal(false);

  readonly loading = signal(false);
  readonly loadingSessions = signal(false);
  readonly error = signal('');

  readonly latestResponse = signal<ResearchResponse | null>(null);
  readonly chatMessages = signal<ChatMessage[]>([]);
  readonly sessions = signal<UiSession[]>([]);

  readonly suggestions = signal<string[]>([
    'Best crop for loamy soil in Missouri this season?',
    'Soyabean vs maize for Illinois this season',
    'Which crop has better near-term price trend in California?',
    'What fertilizer plan fits clay soil and rice?',
  ]);

  ngOnInit(): void {
    this.checkApiStatus();
    this.loadSessions();
  }

  useSuggestion(text: string): void {
    this.query.set(text);
  }

  setShowMeta(value: boolean): void {
    this.showMeta.set(value);
  }

  setQuery(value: string): void {
    this.query.set(value);
  }

  setLocation(value: string): void {
    this.location.set(value);
  }

  setSoilType(value: string): void {
    this.soilType.set(value);
  }

  private addMessage(msg: ChatMessage): void {
    this.chatMessages.update((current) => [...current, msg]);
  }

  private ensureSessionLoaded(sessionId: string): void {
    const exists = this.sessions().some((s) => s.id === sessionId);
    if (!exists) {
      this.loadSessions();
    }
  }

  private toOneLine(text: string): string {
    return text.replace(/\s+/g, ' ').trim();
  }

  private makeSessionLabel(turns: SessionTurn[], fallback: string): string {
    const firstUser = turns.find((t) => t.role === 'user' && (t.content || '').trim());
    const firstAssistant = turns.find((t) => t.role === 'assistant' && (t.content || '').trim());
    const candidate = firstUser?.content || firstAssistant?.content || fallback;
    const oneLine = this.toOneLine(candidate);
    return oneLine.length > 58 ? `${oneLine.slice(0, 58)}...` : oneLine;
  }

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  renderRecommendation(text: string): string {
    const escaped = this.escapeHtml(text);
    return escaped
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br/>');
  }

  submitResearch(): void {
    const trimmedQuery = this.query().trim();
    if (!trimmedQuery) {
      this.error.set('Please enter a query.');
      return;
    }

    this.error.set('');
    this.loading.set(true);

    this.addMessage({ role: 'user', text: trimmedQuery });

    this.api
      .research({
        query: trimmedQuery,
        session_id: this.currentSessionId() || null,
        location: this.location() || null,
        soil_type: this.soilType() || null,
      })
      .subscribe({
        next: (res) => {
          this.latestResponse.set(res);
          this.currentSessionId.set(res.session_id);
          this.ensureSessionLoaded(res.session_id);
          this.addMessage({ role: 'assistant', text: res.recommendation, response: res });
          this.query.set('');
          this.loadSessions();
        },
        error: (err) => {
          const message = err?.error?.detail || 'Failed to fetch research response.';
          this.error.set(message);
          this.addMessage({ role: 'error', text: message });
        },
        complete: () => {
          this.loading.set(false);
        },
      });
  }

  loadSessions(): void {
    this.loadingSessions.set(true);
    this.api.getSessions(30).subscribe({
      next: (res) => {
        const baseSessions = res.sessions || [];
        if (!baseSessions.length) {
          this.sessions.set([]);
          return;
        }

        forkJoin(
          baseSessions.map((session, index) =>
            this.api.getSessionHistory(session.id, 10).pipe(
              map((history) => ({
                ...session,
                label: this.makeSessionLabel(history.turns || [], `Session ${index + 1}`),
              })),
              catchError(() =>
                of({
                  ...session,
                  label: `Session ${index + 1}`,
                })
              )
            )
          )
        ).subscribe((sessionsWithLabels) => this.sessions.set(sessionsWithLabels));
      },
      error: () => {
        this.error.set('Unable to load sessions.');
      },
      complete: () => {
        this.loadingSessions.set(false);
      },
    });
  }

  useSession(sessionId: string): void {
    this.currentSessionId.set(sessionId);
    this.api.getSessionHistory(sessionId, 25).subscribe({
      next: (history) => {
        const rebuilt: ChatMessage[] = (history.turns || []).map((turn: SessionTurn) => ({
          role: turn.role === 'assistant' ? 'assistant' : 'user',
          text: turn.content || '',
        }));
        this.chatMessages.set(rebuilt);
      },
      error: () => {
        this.error.set('Unable to load selected session history.');
      },
    });
  }

  clearSession(): void {
    this.currentSessionId.set('');
    this.latestResponse.set(null);
    this.chatMessages.set([]);
  }

  checkApiStatus(): void {
    this.api.getHealth().subscribe({
      next: (res) => {
        this.apiConnected.set(res.status === 'ok');
      },
      error: () => {
        this.apiConnected.set(false);
      },
    });
  }

  onInputKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (!this.loading()) {
        this.submitResearch();
      }
    }
  }
}
