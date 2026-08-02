import { userApi } from '../api/userApi';

export async function finalizeSession(
  accessToken: string,
  setToken: (t: string) => void,
  setUser: (u: any) => void,
) {
  setToken(accessToken);

  const payload = JSON.parse(atob(accessToken.split('.')[1]));
  const user = await userApi.createOrGet({
    name: payload.user_metadata?.full_name ?? payload.email,
    email: payload.email,
  });
  setUser(user);
}
