import { Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { APP_NAME, BOOKING_LABEL_PLURAL, RESOURCE_LABEL_PLURAL } from '../../core/config';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink],
  template: `
    <header class="header">
      <a routerLink="/" class="logo">{{ appName }}</a>
      <nav class="nav">
        <a routerLink="/">{{ resourceLabelPlural }}</a>
        @if (auth.isSignedIn()) {
          <a routerLink="/my-bookings">My {{ bookingLabelPlural }}</a>
          <span>{{ auth.currentUser()?.name || auth.currentUser()?.email }}</span>
          <button type="button" class="btn" (click)="handleSignOut()">Sign out</button>
        } @else {
          <a routerLink="/sign-in">Sign in</a>
          <a routerLink="/sign-up">Sign up</a>
        }
      </nav>
    </header>
  `,
})
export class HeaderComponent {
  auth = inject(AuthService);
  private router = inject(Router);

  appName = APP_NAME;
  resourceLabelPlural = RESOURCE_LABEL_PLURAL;
  bookingLabelPlural = BOOKING_LABEL_PLURAL;

  handleSignOut(): void {
    this.auth.signOut().subscribe(() => this.router.navigateByUrl('/'));
  }
}
