import { inject } from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import { CanActivateFn, Router } from '@angular/router';
import { filter, map, take } from 'rxjs';

import { AuthService } from './auth.service';

// Waits for the initial session check to resolve before deciding, the
// same way the parent skill's <RequireAuth> renders nothing while
// useSession() is pending - redirecting before the session check resolves
// would bounce a signed-in user to /sign-in on every page load.
export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return toObservable(auth.isPending).pipe(
    filter((pending) => !pending),
    take(1),
    map(() =>
      auth.isSignedIn()
        ? true
        : router.createUrlTree(['/sign-in'], { queryParams: { redirect: state.url } }),
    ),
  );
};
