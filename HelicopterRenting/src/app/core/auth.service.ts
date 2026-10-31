import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { catchError, of, tap } from 'rxjs';

import { User } from './models';

// No baseURL/CORS config needed: in dev, Angular's proxy (proxy.conf.json)
// forwards /api to the backend as if same-origin; in prod, the backend
// serves this build directly from the same origin. See
// references/architecture.md for why the parent skill's React version
// makes the same choice.
@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);

  private userSignal = signal<User | null>(null);
  private pendingSignal = signal(true);

  readonly currentUser = this.userSignal.asReadonly();
  readonly isPending = this.pendingSignal.asReadonly();
  readonly isSignedIn = computed(() => this.userSignal() !== null);

  constructor() {
    this.refreshSession();
  }

  refreshSession(): void {
    this.pendingSignal.set(true);
    this.http
      .get<User>('/api/auth/session')
      .pipe(catchError(() => of(null)))
      .subscribe((user) => {
        this.userSignal.set(user);
        this.pendingSignal.set(false);
      });
  }

  signIn(email: string, password: string) {
    return this.http
      .post<User>('/api/auth/sign-in', { email, password })
      .pipe(tap((user) => this.userSignal.set(user)));
  }

  signUp(name: string, email: string, password: string) {
    return this.http
      .post<User>('/api/auth/sign-up', { name, email, password })
      .pipe(tap((user) => this.userSignal.set(user)));
  }

  signOut() {
    return this.http.post('/api/auth/sign-out', {}).pipe(tap(() => this.userSignal.set(null)));
  }
}
