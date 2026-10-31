import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-sign-up',
  standalone: true,
  imports: [FormsModule, RouterLink],
  template: `
    <div class="page">
      <h1>Sign up</h1>
      <form class="form" (ngSubmit)="handleSubmit()">
        <div class="form-group">
          <label for="name">Name</label>
          <input id="name" name="name" [(ngModel)]="name" required />
        </div>
        <div class="form-group">
          <label for="email">Email</label>
          <input id="email" name="email" type="email" [(ngModel)]="email" required />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            minlength="8"
            [(ngModel)]="password"
            required
          />
        </div>

        @if (error()) {
          <p class="form-error">{{ error() }}</p>
        }

        <button type="submit" class="btn btn-primary" [disabled]="submitting()">
          {{ submitting() ? 'Creating account…' : 'Sign up' }}
        </button>
      </form>
      <p>
        Already have an account?
        <a [routerLink]="'/sign-in'" [queryParams]="{ redirect }">Sign in</a>
      </p>
    </div>
  `,
})
export class SignUpComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  name = '';
  email = '';
  password = '';
  submitting = signal(false);
  error = signal<string | null>(null);
  redirect = this.route.snapshot.queryParamMap.get('redirect') || '/';

  handleSubmit(): void {
    this.submitting.set(true);
    this.error.set(null);

    this.auth.signUp(this.name, this.email, this.password).subscribe({
      next: () => this.router.navigateByUrl(this.redirect),
      error: (err) => {
        this.error.set(err?.error?.detail || 'Failed to sign up');
        this.submitting.set(false);
      },
    });
  }
}
