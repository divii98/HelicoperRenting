import { Component, inject } from '@angular/core';

import { ResourceCardComponent } from '../../components/resource-card/resource-card.component';
import { RESOURCE_LABEL_PLURAL } from '../../core/config';
import { ResourcesService } from '../../core/resources.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [ResourceCardComponent],
  template: `
    <div class="page">
      @if (resourcesService.loading()) {
        <p>Loading {{ resourceLabelPlural.toLowerCase() }}…</p>
      } @else if (resourcesService.error()) {
        <p class="form-error">{{ resourcesService.error() }}</p>
      } @else {
        <h1>{{ resourceLabelPlural }}</h1>
        <div class="resource-grid">
          @for (resource of resourcesService.resources(); track resource.id) {
            <app-resource-card [resource]="resource" />
          }
        </div>
      }
    </div>
  `,
})
export class HomeComponent {
  resourcesService = inject(ResourcesService);
  resourceLabelPlural = RESOURCE_LABEL_PLURAL;
}
