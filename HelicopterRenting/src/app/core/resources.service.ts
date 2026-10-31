import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { catchError, of } from 'rxjs';

import { Resource } from './models';

@Injectable({ providedIn: 'root' })
export class ResourcesService {
  private http = inject(HttpClient);

  private resourcesSignal = signal<Resource[]>([]);
  private loadingSignal = signal(true);
  private errorSignal = signal<string | null>(null);

  readonly resources = this.resourcesSignal.asReadonly();
  readonly loading = this.loadingSignal.asReadonly();
  readonly error = this.errorSignal.asReadonly();

  private byId = computed(() => new Map(this.resourcesSignal().map((r) => [r.id, r])));

  constructor() {
    this.http
      .get<Resource[]>('/api/resources')
      .pipe(
        catchError(() => {
          this.errorSignal.set('Failed to load resources');
          return of<Resource[]>([]);
        }),
      )
      .subscribe((resources) => {
        this.resourcesSignal.set(resources);
        this.loadingSignal.set(false);
      });
  }

  getById(id: number | string): Resource | undefined {
    return this.byId().get(Number(id));
  }
}
