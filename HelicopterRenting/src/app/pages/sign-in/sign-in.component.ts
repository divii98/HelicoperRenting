import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-sign-in',
  standalone: true,
  imports: [FormsModule, RouterLink],
  template: `
    <div class="page">
      <h1>Sign in</h1>
      <form class="form" (ngSubmit)="handleSubmit()">
        <div class="form-group">
          <label for="email">Email</label>
          <input id="email" name="email" type="email" [(ngModel)]="email" required />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input id="password" name="password" type="password" [(ngModel)]="password" required />
        </div>

        @if (error()) {
          <p class="form-error">{{ error() }}</p>
        }

        <button type="submit" class="btn btn-primary" [disabled]="submitting()">
          {{ submitting() ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>
      <p>
        Don't have an account?
        <a [routerLink]="'/sign-up'" [queryParams]="{ redirect }">Sign up</a>
      </p>
    </div>
  `,
})
export class SignInComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  email = '';
  password = '';
  submitting = signal(false);
  error = signal<string | null>(null);
  redirect = this.route.snapshot.queryParamMap.get('redirect') || '/';

  handleSubmit(): void {
    this.submitting.set(true);
    this.error.set(null);

    this.auth.signIn(this.email, this.password).subscribe({
      next: () => this.router.navigateByUrl(this.redirect),
      error: (err) => {
        this.error.set(err?.error?.detail || 'Failed to sign in');
        this.submitting.set(false);
      },
    });
  }
}
