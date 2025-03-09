import { cookies } from 'next/headers';

const AUTH_COOKIE = 'auth_token';

export function getAuthToken(): string | undefined {
  const cookieStore = cookies();
  return cookieStore.get(AUTH_COOKIE)?.value;
}

export function setAuthToken(token: string): void {
  cookies().set(AUTH_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    path: '/'
  });
}

export function removeAuthToken(): void {
  cookies().delete(AUTH_COOKIE);
} 