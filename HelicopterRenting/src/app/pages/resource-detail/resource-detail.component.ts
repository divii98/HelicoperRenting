import { HttpClient } from '@angular/common/http';
import { Component, computed, effect, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { catchError, of } from 'rxjs';

import { BOOKING_LABEL } from '../../core/config';
import { Availability, Booking, Slot } from '../../core/models';
import { AuthService } from '../../core/auth.service';
import { ResourcesService } from '../../core/resources.service';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

@Component({
  selector: 'app-resource-detail',
  standalone: true,
  imports: [],
  template: `
    <div class="page">
      @if (resourcesService.loading()) {
        <p>Loading…</p>
      } @else if (!resource()) {
        <p>Not found.</p>
      } @else {
        <h1>{{ resource()!.name }}</h1>
        <p>{{ resource()!.description }}</p>

        <div class="form-group">
          <label for="date">Date</label>
          <input
            id="date"
            type="date"
            [value]="date()"
            [min]="minDate"
            (change)="onDateChange($event)"
          />
        </div>

        @if (error()) {
          <p class="form-error">{{ error() }}</p>
        }

        @if (loadingSlots()) {
          <p>Loading availability…</p>
        } @else {
          <div class="slot-grid">
            @if (availability()?.slots?.length === 0) {
              <p>No slots configured for this day.</p>
            }
            @for (slot of availability()?.slots ?? []; track slot.slotStart) {
              <button
                type="button"
                class="slot"
                [class.slot-open]="slot.available > 0"
                [class.slot-full]="slot.available <= 0"
                [disabled]="slot.available <= 0 || bookingSlot() === slot.slotStart"
                (click)="handleBook(slot)"
              >
                {{ formatSlotTime(slot.slotStart) }}
                @if (resource()!.capacity > 1) {
                  <span class="slot-capacity"> ({{ slot.available }}/{{ slot.capacity }} left)</span>
                }
              </button>
            }
          </div>
        }
        <p class="hint">Click an open slot to create a {{ bookingLabel.toLowerCase() }}.</p>
      }
    </div>
  `,
})
export class ResourceDetailComponent {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  resourcesService = inject(ResourcesService);

  bookingLabel = BOOKING_LABEL;
  minDate = todayIso();

  private id = this.route.snapshot.paramMap.get('id')!;
  resource = computed(() => this.resourcesService.getById(this.id));
  date = signal(this.minDate);
  availability = signal<Availability | null>(null);
  loadingSlots = signal(true);
  error = signal<string | null>(null);
  bookingSlot = signal<string | null>(null);

  constructor() {
    // Re-fetches availability whenever the resolved resource or the
    // selected date changes - the equivalent of the parent skill's
    // `useEffect(..., [resource, date])`.
    effect(() => {
      const resource = this.resource();
      const date = this.date();
      if (!resource) return;
      this.loadAvailability(resource.id, date);
    });
  }

  private loadAvailability(resourceId: number, date: string): void {
    this.error.set(null);
    this.loadingSlots.set(true);
    this.http
      .get<Availability>(`/api/resources/${resourceId}/availability?date=${date}`)
      .pipe(
        catchError(() => {
          this.error.set('Failed to load availability');
          return of(null);
        }),
      )
      .subscribe((availability) => {
        this.availability.set(availability);
        this.loadingSlots.set(false);
      });
  }

  private refreshAvailability(): void {
    const resource = this.resource();
    if (resource) this.loadAvailability(resource.id, this.date());
  }

  onDateChange(event: Event): void {
    this.date.set((event.target as HTMLInputElement).value);
  }

  formatSlotTime(iso: string): string {
    return new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  }

  handleBook(slot: Slot): void {
    const resource = this.resource();
    if (!resource) return;

    if (!this.auth.isSignedIn()) {
      this.router.navigate(['/sign-in'], {
        queryParams: { redirect: `/resource/${resource.id}` },
      });
      return;
    }

    this.bookingSlot.set(slot.slotStart);
    this.error.set(null);

    this.http
      .post<Booking>('/api/bookings', { resourceId: resource.id, slotStart: slot.slotStart })
      .subscribe({
        next: (booking) => {
          this.bookingSlot.set(null);
          this.router.navigate(['/booking-confirmation', booking.id], {
            state: { booking, resourceName: resource.name },
          });
        },
        error: (err) => {
          this.error.set(err?.error?.detail || 'Failed to book slot');
          this.bookingSlot.set(null);
          // The slot we tried is probably gone now (someone else took it)
          // - refetch so the grid reflects reality instead of staying
          // stale.
          this.refreshAvailability();
        },
      });
  }
}
