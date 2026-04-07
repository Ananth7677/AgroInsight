import { Routes } from '@angular/router';

import { HomePage } from './pages/home/home.page';
import { ResearchPage } from './pages/research/research.page';

export const routes: Routes = [
	{ path: '', component: HomePage, pathMatch: 'full' },
	{ path: 'research', component: ResearchPage },
	{ path: '**', redirectTo: '' },
];
