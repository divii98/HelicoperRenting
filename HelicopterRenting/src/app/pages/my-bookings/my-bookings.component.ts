import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';

import { BOOKING_LABEL_PLURAL } from '../../core/config';
import { Booking } from '../../core/models';

@Component({
  selector: 'app-my-bookings',
  standalone: true,
  imports: [],
  template: `
    <div class="page">
      <h1>My {{ bookingLabelPlural }}</h1>
      @if (loading()) {
        <p>Loading…</p>
      } @else {
        @if (error()) {
          <p class="form-error">{{ error() }}</p>
        }
        @if (bookings().length === 0) {
          <p>No bookings yet.</p>
        }
        <ul class="booking-list">
          @for (booking of bookings(); track booking.id) {
            <li class="booking-item">
              <div>
                <strong>{{ booking.resource_name }}</strong>
                <div>{{ formatSlot(booking.slot_start) }}</div>
                <div class="status status-{{ booking.status }}">{{ booking.status }}</div>
              </div>
              @if (booking.status === 'confirmed' && isFuture(booking.slot_start)) {
                <button type="button" class="btn" (click)="handleCancel(booking.id)">
                  Cancel
                </button>
              }
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class MyBookingsComponent implements OnInit {
  private http = inject(HttpClient);

  bookingLabelPlural = BOOKING_LABEL_PLURAL;
  bookings = signal<Booking[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.http.get<Booking[]>('/api/bookings/mine').subscribe({
      next: (bookings) => {
        this.bookings.set(bookings);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load bookings');
        this.loading.set(false);
      },
    });
  }

  formatSlot(iso: string): string {
    return new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
  }

  isFuture(iso: string): boolean {
    return new Date(iso) > new Date();
  }

  handleCancel(id: number): void {
    if (!window.confirm('Cancel this booking?')) return;
    this.http.patch(`/api/bookings/${id}/cancel`, {}).subscribe(() => {
      this.bookings.update((prev) =>
        prev.map((b) => (b.id === id ? { ...b, status: 'cancelled' } : b)),
      );
    });
  }
}
