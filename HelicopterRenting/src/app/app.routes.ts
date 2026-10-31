import { Routes } from '@angular/router';

import { authGuard } from './core/auth.guard';
import { BookingConfirmationComponent } from './pages/booking-confirmation/booking-confirmation.component';
import { HomeComponent } from './pages/home/home.component';
import { MyBookingsComponent } from './pages/my-bookings/my-bookings.component';
import { ResourceDetailComponent } from './pages/resource-detail/resource-detail.component';
import { SignInComponent } from './pages/sign-in/sign-in.component';
import { SignUpComponent } from './pages/sign-up/sign-up.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'resource/:id', component: ResourceDetailComponent },
  { path: 'sign-in', component: SignInComponent },
  { path: 'sign-up', component: SignUpComponent },
  { path: 'my-bookings', component: MyBookingsComponent, canActivate: [authGuard] },
  { path: 'booking-confirmation/:id', component: BookingConfirmationComponent },
];
