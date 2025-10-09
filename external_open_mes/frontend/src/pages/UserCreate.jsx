import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import authFetch from '../utils/api';

const initialFormState = {
  custom_id: '',
  username: '',
  email: '',
  is_staff: false,
  is_superuser: false,
  is_active: true,
};

const UserCreate = () => {
  const [formData, setFormData] = useState(initialFormState);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setError('');
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const payload = {
        custom_id: formData.custom_id.trim(),
        username: formData.username.trim(),
        email: formData.email.trim() || null,
        is_staff: formData.is_staff,
        is_superuser: formData.is_superuser,
        is_active: formData.is_active,
      };

      const response = await authFetch('/api/users/', {
        method: 'POST',
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
          'ユーザーの作成に失敗しました。';
        throw new Error(detail);
      }

      navigate('/user/management', {
        state: { message: 'ユーザーを作成しました。', messageType: 'success' },
      });
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  };

  return (
    <div className="container">
      <h1 className="mb-4">ユーザー作成</h1>
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}
      <form onSubmit={handleSubmit} className="row g-3">
        <div className="col-md-6">
          <label htmlFor="custom_id" className="form-label">
            専用ID<span className="text-danger">*</span>
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
            value={formData.email}
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
            {submitting ? '作成中...' : '作成'}
          </button>
        </div>
      </form>
      <p className="mt-3 text-muted small">
        初期パスワードは未設定です。作成後にユーザーへ通知し、パスワード設定を行ってください。
      </p>
    </div>
  );
};

export default UserCreate;
