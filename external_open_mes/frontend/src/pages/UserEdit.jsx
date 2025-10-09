import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import authFetch from '../utils/api';

const UserEdit = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const fetchUser = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await authFetch(`/api/users/${id}/`);
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        const detail =
          data?.detail ||
          Object.values(data || {})
            .flat()
            .join(' ') ||
          'ユーザー情報の取得に失敗しました。';
        throw new Error(detail);
      }
      const data = await response.json();
      setFormData({
        custom_id: data.custom_id || '',
        username: data.username || '',
        email: data.email || '',
        is_staff: data.is_staff || false,
        is_superuser: data.is_superuser || false,
        is_active: data.is_active || false,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!formData) return;
    setSubmitting(true);
    setError('');
    try {
      const payload = {
        custom_id: formData.custom_id.trim(),
        username: formData.username.trim(),
        email: formData.email.trim() || null,
        is_staff: formData.is_staff,
        is_superuser: formData.is_superuser,
        is_active: formData.is_active,
      };

      const response = await authFetch(`/api/users/${id}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        const detail =
          data?.detail ||
          Object.values(data || {})
            .flat()
            .join(' ') ||
          'ユーザーの更新に失敗しました。';
        throw new Error(detail);
      }

      navigate('/user/management', {
        state: { message: 'ユーザー情報を更新しました。', messageType: 'success' },
      });
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div>読み込み中...</div>;
  }

  if (!formData) {
    return (
      <div className="alert alert-danger" role="alert">
        {error || 'ユーザー情報を読み込めませんでした。'}
      </div>
    );
  }

  return (
    <div className="container">
      <h1 className="mb-4">ユーザー編集</h1>
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}
      <form onSubmit={handleSubmit} className="row g-3">
        <div className="col-md-6">
          <label htmlFor="custom_id" className="form-label">
            専用ID
          </label>
          <input
            id="custom_id"
            name="custom_id"
            className="form-control"
            value={formData.custom_id}
            onChange={handleChange}
            required
          />
        </div>
        <div className="col-md-6">
          <label htmlFor="username" className="form-label">
            表示名
          </label>
          <input
            id="username"
            name="username"
            className="form-control"
            value={formData.username}
            onChange={handleChange}
          />
        </div>
        <div className="col-md-6">
          <label htmlFor="email" className="form-label">
            メールアドレス
          </label>
          <input
            id="email"
            name="email"
            type="email"
            className="form-control"
            value={formData.email || ''}
            onChange={handleChange}
          />
        </div>
        <div className="col-md-6 d-flex align-items-end">
          <div className="form-check me-3">
            <input
              id="is_active"
              name="is_active"
              type="checkbox"
              className="form-check-input"
              checked={formData.is_active}
              onChange={handleChange}
            />
            <label className="form-check-label" htmlFor="is_active">
              有効
            </label>
          </div>
          <div className="form-check me-3">
            <input
              id="is_staff"
              name="is_staff"
              type="checkbox"
              className="form-check-input"
              checked={formData.is_staff}
              onChange={handleChange}
            />
            <label className="form-check-label" htmlFor="is_staff">
              スタッフ
            </label>
          </div>
          <div className="form-check">
            <input
              id="is_superuser"
              name="is_superuser"
              type="checkbox"
              className="form-check-input"
              checked={formData.is_superuser}
              onChange={handleChange}
            />
            <label className="form-check-label" htmlFor="is_superuser">
              スーパーユーザー
            </label>
          </div>
        </div>
        <div className="col-12 d-flex justify-content-end">
          <button
            type="button"
            className="btn btn-secondary me-2"
            onClick={() => navigate('/user/management')}
            disabled={submitting}
          >
            キャンセル
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? '更新中...' : '更新'}
          </button>
        </div>
      </form>
      <p className="mt-3 text-muted small">
        パスワードの変更は「ユーザー設定」ページまたは API を利用して行ってください。
      </p>
    </div>
  );
};

export default UserEdit;
