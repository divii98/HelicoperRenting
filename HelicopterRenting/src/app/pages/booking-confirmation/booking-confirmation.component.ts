import { Location } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { BOOKING_LABEL } from '../../core/config';
import { Booking } from '../../core/models';

@Component({
  selector: 'app-booking-confirmation',
  standalone: true,
  imports: [],
  template: `
    <div class="page">
      @if (error()) {
        <p class="form-error">{{ error() }}</p>
      } @else if (!booking()) {
        <p>Loading…</p>
      } @else {
        <h1>{{ bookingLabel }} confirmed</h1>
        <p>{{ resourceName() }}</p>
        <p>{{ formatSlot(booking()!.slot_start) }}</p>
        <p>Confirmation #{{ booking()!.id }}</p>
      }
    </div>
  `,
})
export class BookingConfirmationComponent implements OnInit {
  private http = inject(HttpClient);
  private route = inject(ActivatedRoute);
  private location = inject(Location);

  bookingLabel = BOOKING_LABEL;
  booking = signal<Booking | null>(null);
  resourceName = signal<string | null>(null);
  error = signal<string | null>(null);

  ngOnInit(): void {
    // Booking data arrives via router state right after a successful POST
    // (no extra request needed) - Angular's Router stores navigation
    // `state` in the browser's History API, read back here via
    // `Location.getState()`. On a hard refresh, state is gone, so this
    // falls back to fetching the authenticated, ownership-scoped
    // GET /api/bookings/:id.
    const state = this.location.getState() as
      | { booking?: Booking; resourceName?: string }
      | undefined;

    if (state?.booking) {
      this.booking.set(state.booking);
      this.resourceName.set(state.resourceName ?? null);
      return;
    }

    const id = this.route.snapshot.paramMap.get('id');
    this.http.get<Booking>(`/api/bookings/${id}`).subscribe({
      next: (booking) => {
        this.booking.set(booking);
        this.resourceName.set(booking.resource_name);
      },
      error: (err) => {
        this.error.set(
          err.status === 401
            ? `Sign in to view this ${this.bookingLabel.toLowerCase()}`
            : `${this.bookingLabel} not found`,
        );
      },
    });
  }

  formatSlot(iso: string): string {
    return new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
  }
}
