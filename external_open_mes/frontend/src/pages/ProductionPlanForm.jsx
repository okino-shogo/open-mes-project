import React, { useState, useEffect } from 'react';
import authFetch from '../utils/api.js';

const ProductionPlanForm = ({ planId, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    qr_code: '',
    reception_no: '',
    additional_no: '',
    customer_name: '',
    site_name: '',
    additional_content: '',
    product_name: '',
    process: '',
    planned_quantity: '',
    manufacturing_scheduled_date: '',
    planned_shipment_date: '',
    delivery_date: '',
    slit_scheduled_date: '',
    cut_scheduled_date: '',
    base_material_cut_scheduled_date: '',
    molder_scheduled_date: '',
    vcut_wrapping_scheduled_date: '',
    post_processing_scheduled_date: '',
    packing_scheduled_date: '',
    veneer_scheduled_date: '',
    cut_veneer_scheduled_date: '',
    remarks: ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});

  // 編集モードの場合、既存データを取得
  useEffect(() => {
    if (planId) {
      loadPlanData(planId);
    }
  }, [planId]);

  const loadPlanData = async (id) => {
    setLoading(true);
    try {
      const response = await authFetch(`/api/production/plans/${id}/`);
      if (!response.ok) throw new Error('データの取得に失敗しました');
      const data = await response.json();
      setFormData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // エラーをクリア
    if (validationErrors[name]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  // QRコード自動生成
  const generateQRCode = () => {
    const { reception_no, additional_no } = formData;
    if (reception_no && additional_no) {
      // 追加Noを4桁にゼロパディング
      const paddedAdditionalNo = additional_no.padStart(4, '0');
      const qrCode = reception_no + paddedAdditionalNo;
      setFormData(prev => ({ ...prev, qr_code: qrCode }));
    }
  };

  // 受付No/追加No変更時にQRコード自動生成
  useEffect(() => {
    generateQRCode();
  }, [formData.reception_no, formData.additional_no]);

  // バリデーション
  const validate = () => {
    const errors = {};

    // QRコード: 必須、数字のみ
    if (!formData.qr_code) {
      errors.qr_code = 'QRコードを入力してください';
    } else if (!/^\d+$/.test(formData.qr_code)) {
      errors.qr_code = 'QRコードは数字のみで入力してください';
    }

    // 受付No: 必須、5桁
    if (!formData.reception_no) {
      errors.reception_no = '受付Noを入力してください';
    } else if (!/^\d{5}$/.test(formData.reception_no)) {
      errors.reception_no = '受付Noは5桁の数字で入力してください';
    }

    // 追加No: 必須、数字のみ
    if (!formData.additional_no) {
      errors.additional_no = '追加Noを入力してください';
    } else if (!/^\d+$/.test(formData.additional_no)) {
      errors.additional_no = '追加Noは数字のみで入力してください';
    }

    // 品名: 必須
    if (!formData.product_name) {
      errors.product_name = '品名を入力してください';
    }

    // 工程: 必須
    if (!formData.process) {
      errors.process = '工程を選択してください';
    }

    // 数量: 正の整数
    if (formData.planned_quantity && formData.planned_quantity <= 0) {
      errors.planned_quantity = '数量は正の整数で入力してください';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) {
      setError('入力内容に誤りがあります');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const url = planId
        ? `/api/production/plans/${planId}/`
        : '/api/production/plans/';

      const method = planId ? 'PUT' : 'POST';

      // データ型変換とクリーニング
      const cleanedData = Object.fromEntries(
        Object.entries(formData).map(([key, value]) => {
          // 空文字列はnullに変換
          if (value === '') return [key, null];

          // 数量フィールドは整数に変換
          if (key === 'planned_quantity' && value !== null) {
            return [key, parseInt(value, 10)];
          }

          return [key, value];
        })
      );

      // デバッグ用: 送信データをログ出力
      console.log('📤 送信データ:', JSON.stringify(cleanedData, null, 2));

      const response = await authFetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cleanedData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('❌ APIエラー:', errorData);

        // バリデーションエラーの詳細を表示
        if (errorData && typeof errorData === 'object') {
          const errorMessages = Object.entries(errorData)
            .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`)
            .join('\n');
          throw new Error(errorMessages || '保存に失敗しました');
        }

        throw new Error(errorData.detail || '保存に失敗しました');
      }

      const savedData = await response.json();
      if (onSave) onSave(savedData);
      if (onClose) onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && planId) {
    return <div className="text-center p-4">読み込み中...</div>;
  }

  return (
    <div className="production-plan-form">
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}

        {/* セクション1: 識別情報 */}
        <div className="card mb-3">
          <div className="card-header">
            <h5 className="mb-0">識別情報</h5>
          </div>
          <div className="card-body">
            <div className="row">
              <div className="col-md-4 mb-3">
                <label className="form-label">QRコード <span className="text-danger">*</span></label>
                <input
                  type="text"
                  className={`form-control ${validationErrors.qr_code ? 'is-invalid' : ''}`}
                  name="qr_code"
                  value={formData.qr_code}
                  onChange={handleChange}
                  placeholder="自動生成されます"
                />
                {validationErrors.qr_code && (
                  <div className="invalid-feedback">{validationErrors.qr_code}</div>
                )}
              </div>
              <div className="col-md-4 mb-3">
                <label className="form-label">受付No <span className="text-danger">*</span></label>
                <input
                  type="text"
                  className={`form-control ${validationErrors.reception_no ? 'is-invalid' : ''}`}
                  name="reception_no"
                  value={formData.reception_no}
                  onChange={handleChange}
                  placeholder="例: 25599"
                  maxLength="5"
                />
                {validationErrors.reception_no && (
                  <div className="invalid-feedback">{validationErrors.reception_no}</div>
                )}
              </div>
              <div className="col-md-4 mb-3">
                <label className="form-label">追加No <span className="text-danger">*</span></label>
                <input
                  type="text"
                  className={`form-control ${validationErrors.additional_no ? 'is-invalid' : ''}`}
                  name="additional_no"
                  value={formData.additional_no}
                  onChange={handleChange}
                  placeholder="例: 1"
                />
                {validationErrors.additional_no && (
                  <div className="invalid-feedback">{validationErrors.additional_no}</div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* セクション2: 基本情報 */}
        <div className="card mb-3">
          <div className="card-header">
            <h5 className="mb-0">基本情報</h5>
          </div>
          <div className="card-body">
            <div className="row">
              <div className="col-md-6 mb-3">
                <label className="form-label">得意先名</label>
                <input
                  type="text"
                  className="form-control"
                  name="customer_name"
                  value={formData.customer_name}
                  onChange={handleChange}
                  placeholder="例: (株)長谷工ファニシング"
                />
              </div>
              <div className="col-md-6 mb-3">
                <label className="form-label">現場名</label>
                <input
                  type="text"
                  className="form-control"
                  name="site_name"
                  value={formData.site_name}
                  onChange={handleChange}
                  placeholder="例: 東京日商E八王子市東浅川町"
                />
              </div>
            </div>
            <div className="row">
              <div className="col-md-4 mb-3">
                <label className="form-label">品名 <span className="text-danger">*</span></label>
                <input
                  type="text"
                  className={`form-control ${validationErrors.product_name ? 'is-invalid' : ''}`}
                  name="product_name"
                  value={formData.product_name}
                  onChange={handleChange}
                  placeholder="例: WD (V)(ラ)"
                  list="product-name-list"
                />
                <datalist id="product-name-list">
                  <option value="WD (V)(ラ)" />
                  <option value="AW (V)" />
                  <option value="AW (V)(ラ)" />
                  <option value="VJ折れ戸 扉 (V)(ラ)" />
                  <option value="基材 (V)" />
                  <option value="カウンター (V)" />
                  <option value="CB (V)(ラ)" />
                </datalist>
                {validationErrors.product_name && (
                  <div className="invalid-feedback">{validationErrors.product_name}</div>
                )}
              </div>
              <div className="col-md-4 mb-3">
                <label className="form-label">工程 <span className="text-danger">*</span></label>
                <select
                  className={`form-select ${validationErrors.process ? 'is-invalid' : ''}`}
                  name="process"
                  value={formData.process}
                  onChange={handleChange}
                >
                  <option value="">選択してください</option>
                  <option value="スリット">スリット</option>
                  <option value="カット">カット</option>
                  <option value="基材カット">基材カット</option>
                  <option value="モルダー">モルダー</option>
                  <option value="Vカット">Vカット</option>
                  <option value="ラッピング">ラッピング</option>
                  <option value="後加工">後加工</option>
                  <option value="梱包">梱包</option>
                  <option value="扉">扉</option>
                </select>
                {validationErrors.process && (
                  <div className="invalid-feedback">{validationErrors.process}</div>
                )}
              </div>
              <div className="col-md-4 mb-3">
                <label className="form-label">数量</label>
                <input
                  type="number"
                  className={`form-control ${validationErrors.planned_quantity ? 'is-invalid' : ''}`}
                  name="planned_quantity"
                  value={formData.planned_quantity}
                  onChange={handleChange}
                  min="1"
                  placeholder="例: 49"
                />
                {validationErrors.planned_quantity && (
                  <div className="invalid-feedback">{validationErrors.planned_quantity}</div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* セクション3: 追加内容 */}
        <div className="card mb-3">
          <div className="card-header">
            <h5 className="mb-0">追加内容</h5>
          </div>
          <div className="card-body">
            <textarea
              className="form-control"
              name="additional_content"
              value={formData.additional_content}
              onChange={handleChange}
              rows="3"
              placeholder="例: -16~19芯材加工用"
            />
          </div>
        </div>

        {/* セクション4: 日程情報 */}
        <div className="card mb-3">
          <div className="card-header">
            <h5 className="mb-0">日程情報</h5>
          </div>
          <div className="card-body">
            <div className="row">
              <div className="col-md-4 mb-3">
                <label className="form-label">製造予定日</label>
                <input
                  type="date"
                  className="form-control"
                  name="manufacturing_scheduled_date"
                  value={formData.manufacturing_scheduled_date}
                  onChange={handleChange}
                />
              </div>
              <div className="col-md-4 mb-3">
                <label className="form-label">出荷予定日</label>
                <input
                  type="date"
                  className="form-control"
                  name="planned_shipment_date"
                  value={formData.planned_shipment_date}
                  onChange={handleChange}
                />
              </div>
              <div className="col-md-4 mb-3">
                <label className="form-label">納品日</label>
                <input
                  type="date"
                  className="form-control"
                  name="delivery_date"
                  value={formData.delivery_date}
                  onChange={handleChange}
                />
              </div>
            </div>

            {/* 工程予定日（アコーディオン） */}
            <div className="accordion mt-3" id="processScheduleAccordion">
              <div className="accordion-item">
                <h2 className="accordion-header">
                  <button
                    className="accordion-button collapsed"
                    type="button"
                    data-bs-toggle="collapse"
                    data-bs-target="#processScheduleBody"
                  >
                    工程予定日の詳細設定
                  </button>
                </h2>
                <div id="processScheduleBody" className="accordion-collapse collapse">
                  <div className="accordion-body">
                    <div className="row">
                      <div className="col-md-4 mb-3">
                        <label className="form-label">スリット予定日</label>
                        <input
                          type="date"
                          className="form-control"
                          name="slit_scheduled_date"
                          value={formData.slit_scheduled_date}
                          onChange={handleChange}
                        />
                      </div>
                      <div className="col-md-4 mb-3">
                        <label className="form-label">カット予定日</label>
                        <input
                          type="date"
                          className="form-control"
                          name="cut_scheduled_date"
                          value={formData.cut_scheduled_date}
                          onChange={handleChange}
                        />
                      </div>
                      <div className="col-md-4 mb-3">
                        <label className="form-label">基材カット予定日</label>
                        <input
                          type="date"
                          className="form-control"
                          name="base_material_cut_scheduled_date"
                          value={formData.base_material_cut_scheduled_date}
                          onChange={handleChange}
                        />
                      </div>
                    </div>
                    <div className="row">
                      <div className="col-md-4 mb-3">
                        <label className="form-label">モルダー予定日</label>
                        <input
                          type="date"
                          className="form-control"
                          name="molder_scheduled_date"
                          value={formData.molder_scheduled_date}
                          onChange={handleChange}
                        />
                      </div>
                      <div className="col-md-4 mb-3">
                        <label className="form-label">Vカットラッピング予定日</label>
                        <input
                          type="date"
                          className="form-control"
                          name="vcut_wrapping_scheduled_date"
                          value={formData.vcut_wrapping_scheduled_date}
                          onChange={handleChange}
                        />
                      </div>
                      <div className="col-md-4 mb-3">
                        <label className="form-label">後加工予定日</label>
                        <input
                          type="date"
                          className="form-control"
                          name="post_processing_scheduled_date"
                          value={formData.post_processing_scheduled_date}
                          onChange={handleChange}
                        />
                      </div>
                    </div>
                    <div className="row">
                      <div className="col-md-4 mb-3">
                        <label className="form-label">梱包予定日</label>
                        <input
                          type="date"
                          className="form-control"
                          name="packing_scheduled_date"
                          value={formData.packing_scheduled_date}
                          onChange={handleChange}
                        />
                      </div>
                      <div className="col-md-4 mb-3">
                        <label className="form-label">化粧板貼予定日</label>
                        <input
                          type="date"
                          className="form-control"
                          name="veneer_scheduled_date"
                          value={formData.veneer_scheduled_date}
                          onChange={handleChange}
                        />
                      </div>
                      <div className="col-md-4 mb-3">
                        <label className="form-label">カット化粧板予定日</label>
                        <input
                          type="date"
                          className="form-control"
                          name="cut_veneer_scheduled_date"
                          value={formData.cut_veneer_scheduled_date}
                          onChange={handleChange}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 備考 */}
        <div className="card mb-3">
          <div className="card-header">
            <h5 className="mb-0">備考</h5>
          </div>
          <div className="card-body">
            <textarea
              className="form-control"
              name="remarks"
              value={formData.remarks}
              onChange={handleChange}
              rows="3"
              placeholder="その他の備考"
            />
          </div>
        </div>

        {/* ボタン */}
        <div className="d-flex justify-content-end gap-2">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
            disabled={loading}
          >
            キャンセル
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? '保存中...' : (planId ? '更新' : '登録')}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProductionPlanForm;
