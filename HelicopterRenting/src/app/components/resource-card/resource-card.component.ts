import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Resource } from '../../core/models';

@Component({
  selector: 'app-resource-card',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a [routerLink]="['/resource', resource.id]" class="resource-card">
      <h3>{{ resource.name }}</h3>
      <p class="resource-category">{{ resource.category }}</p>
      <p>{{ resource.description }}</p>
      @if (resource.price_cents > 0) {
        <p class="resource-price">\${{ (resource.price_cents / 100).toFixed(2) }} / slot</p>
      }
    </a>
  `,
})
export class ResourceCardComponent {
  @Input({ required: true }) resource!: Resource;
}
