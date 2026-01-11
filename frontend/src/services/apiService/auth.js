import api from './api';
import { getAccessToken } from '../../hooks/getTokens';

// check auth
// if auth=false, user is not auth
export async function getAuth() {
  try {
    const accessToken = getAccessToken();

    if (!accessToken) {
      return {
        "message": "Access token not found",
        "auth": false,
        "expire": false
      }
    }

    const res = await api.get(`/protected`);

    return {
      "message": res.data.message,
      "auth": res.data.auth,
      "expire": res.data.expire,
    }

  } catch (ex) {
    const data = ex.response?.data
    if (ex.response?.status === 401) {
      // if token is expired
      if (data.expire) {
        return {
          "message": data.message,
          "auth": false,
          "expire": true,
        }
      } else {
        // token is invalid / missing
        return {
          "message": data.message,
          "auth": false,
          "expire": false,
        }
      }
    }
    console.error(ex.response?.data || ex.message);
  }
};


export const login = async (creds) => {
  try {
    const res = await api.post("/login", creds.formData);

    localStorage.setItem("access_token", res.data.access_token);
    window.location.href = "/";
  } catch (ex) {
    if (ex.response.status === 400) {
      creds.changeMessageError(ex.response.data.message);
    }
    console.error(ex);
  }
}

export const register = async (creds) => {
  try {
    const res = await api.post("/register", creds.formData)

    creds.successSubmit();
  } catch (errors) {

    if (errors.response?.status == 400) {
      errors.response.data.detail.forEach((error) => {
        if (error.field === "name" && error.code === "user_exists") {
          creds.changeMessageNameError();
        } else if (error.field === "password" && error.code === "passwords_mismatch") {
          creds.changeMessagePasswordError();
        }
      })
    }
    console.error(errors);
  }
}


export const logout = async (creds) => {
  const res = await api.post("/logout");

  localStorage.removeItem('access_token');
  creds.setAuthFalse();

  return res
}
