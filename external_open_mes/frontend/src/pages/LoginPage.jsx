import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './LoginPage.css'; // Add some basic styling

const LoginPage = ({ onLoginSuccess, isAuthenticated }) => {
  const [customId, setCustomId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || "/";

  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    try {
      console.log('🔐 ログイン試行:', { username: customId });

      // Token認証エンドポイントを使用 (JWT認証ではなくDRF Token認証)
      const response = await fetch('/api/token-auth/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // usernameフィールドでcustom_idを送信
        body: JSON.stringify({ username: customId, password }),
      });

      console.log('📡 レスポンスステータス:', response.status);

      const data = await response.json();
      console.log('📦 レスポンスデータ:', data);

      if (response.ok) {
        console.log('✅ ログイン成功');
        // DRF Tokenをaccess_tokenとして保存
        localStorage.setItem('access_token', data.token);
        // Appコンポーネントにログイン成功を通知
        await onLoginSuccess();
      } else {
        console.error('❌ ログイン失敗:', data);
        let errorMessage = 'Login failed. Please check your credentials and try again.'; // Default message
        if (data) {
            if (data.non_field_errors) {
                errorMessage = data.non_field_errors.join(' ');
            } else if (data.detail) {
                errorMessage = data.detail;
            } else if (typeof data === 'object' && !Array.isArray(data) && Object.keys(data).length > 0) {
                // Handle field-specific errors (e.g., {'password': ['This field is required.']})
                const fieldErrors = Object.entries(data).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(' ') : String(value)}`).join('; ');
                if (fieldErrors) errorMessage = fieldErrors;
            }
        }
        setError(errorMessage);
      }
    } catch (err) {
      console.error('Login request failed:', err);
      setError('An error occurred during login. Please try again later.');
    }
  };

  if (isAuthenticated) {
    return null; // Or a loading spinner, while the redirect happens
  }

  return (
    <div className="login-page-container">
      <div className="login-card">
        <h2 className="login-title">みんなのMES</h2>
        {error && <div className="alert alert-danger">{error}</div>}
        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <input
              type="text"
              id="custom_id"
              className="form-control"
              placeholder="ID"
              value={customId}
              onChange={(e) => setCustomId(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <input
              type="password"
              id="password"
              className="form-control"
              placeholder="パスワード"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <button
              type="submit"
              className="btn btn-primary btn-block"
              style={{ backgroundColor: '#007bff', borderColor: '#007bff' }}
            >
              ログイン
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;