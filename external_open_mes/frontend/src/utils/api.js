import { getCookie } from './cookies';

const authFetch = async (url, options = {}) => {
  let accessToken = localStorage.getItem('access_token');

  const headers = {
    ...options.headers,
  };

  // FormDataの場合、ブラウザが自動でContent-Typeとboundaryを設定するので、
  // こちらで 'Content-Type': 'application/json' を設定しないようにする。
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (accessToken) {
    headers['Authorization'] = `Token ${accessToken}`;
  }

  // CSRFが必要なリクエスト（セッション認証との併用など）のために残す
  const csrfToken = getCookie('csrftoken');
  if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method?.toUpperCase())) {
      headers['X-CSRFToken'] = csrfToken;
  }

  let response = await fetch(url, { ...options, headers });

  // 401エラーの場合はログアウト (Token認証にはリフレッシュ機能がない)
  if (response.status === 401 && accessToken) {
    localStorage.removeItem('access_token');
    window.dispatchEvent(new Event('logout'));
    return Promise.reject(new Error('Authentication failed. Please login again.'));
  }

  return response;
};

export default authFetch;