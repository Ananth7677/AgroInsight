import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { HealthResponse } from '../interfaces/health.interfaces';
import { ResearchRequest, ResearchResponse } from '../interfaces/research.interfaces';
import { SessionHistoryResponse, SessionsResponse } from '../interfaces/session.interfaces';

@Injectable({ providedIn: 'root' })
export class ResearchApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://127.0.0.1:8001';

  research(payload: ResearchRequest): Observable<ResearchResponse> {
    return this.http.post<ResearchResponse>(`${this.baseUrl}/research`, payload);
  }

  getHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.baseUrl}/health`);
  }

  getSessions(limit = 20): Observable<SessionsResponse> {
    return this.http.get<SessionsResponse>(`${this.baseUrl}/sessions?limit=${limit}`);
  }

  getSessionHistory(sessionId: string, limit = 20): Observable<SessionHistoryResponse> {
    return this.http.get<SessionHistoryResponse>(`${this.baseUrl}/sessions/${sessionId}/history?limit=${limit}`);
  }
}
