# users/middleware.py

from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy # reverse_lazy を追加
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages # メッセージフレームワークをインポート
from django.conf import settings # settings をインポート

class PasswordExpirationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # ログインしていないユーザーはチェック対象外
        if not request.user.is_authenticated:
            return None

        # パスワード変更関連のURLとログアウトURLは除外リストに追加
        # 無限リダイレクトループを防ぐため
        exempt_url_names = [
            'password_change',
            'password_change_done',
            'users_logout',
            # 必要であれば管理サイトのURLなども追加
            # 'admin:login',
            # 'admin:logout',
        ]
        # settings.py で除外URL名をカスタマイズ可能にする場合
        # exempt_url_names.extend(getattr(settings, 'PASSWORD_EXPIRATION_EXEMPT_URL_NAMES', []))

        # 現在のURLの名前を取得しようと試みる
        try:
            current_url_name = request.resolver_match.url_name if request.resolver_match else None
        except Exception: # resolver_match が存在しない場合など
            current_url_name = None

        # 除外リストに含まれるURL名の場合はチェックしない
        if current_url_name in exempt_url_names:
            return None

        # is_password_expired プロパティが存在し、True かどうかをチェック
        # スーパーユーザーは有効期限チェックをスキップするオプション (必要に応じて)
        # if request.user.is_superuser:
        #     return None
        if hasattr(request.user, 'is_password_expired') and request.user.is_password_expired:
            # パスワード変更を促すメッセージを表示
            messages.warning(request, 'パスワードの有効期限が切れています。新しいパスワードを設定してください。')
            # パスワード変更ページにリダイレクト
            return redirect(reverse_lazy('password_change')) # reverse_lazy を使用

        # 上記以外の場合は通常通り処理を続行
        return None
