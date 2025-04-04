import uuid
from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.validators import UnicodeUsernameValidator

# マネージャー用
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, custom_id, email, password, **extra_fields):
        if not custom_id:
            raise ValueError('専用IDは必須です。')
        # emailが必須でなくなったので、チェックを削除
        email = self.normalize_email(email) if email else ''
        user = self.model(custom_id=custom_id, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, custom_id, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(custom_id, email, password, **extra_fields)

    def create_superuser(self, custom_id, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('スーパーユーザーは is_staff=True である必要があります。')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('スーパーユーザーは is_superuser=True である必要があります。')

        return self._create_user(custom_id, email, password, **extra_fields)

# カスタムユーザー
class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 専用IDフィールド
    custom_id = models.CharField(
        _('custom id'),
        max_length=50,
        unique=True,
        help_text=_('ログインに使用する専用ID。')
    )
    
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        blank=True,
        validators=[username_validator],
        help_text=_('表示用のユーザー名。')
    )
    
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), unique=True, blank=True)
    
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('管理サイトにログインできるかどうか。'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('アクティブなユーザーかどうか。')
    )
    is_planet_culc = models.BooleanField(
        _('planet_culc'),
        default=False,
        help_text=_('planet culc flag')
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    # ログインに使用するフィールドを専用IDに変更
    USERNAME_FIELD = 'custom_id'
    REQUIRED_FIELDS = []  # emailを必須項目から外す

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        from django.core.mail import send_mail
        send_mail(subject, message, from_email, [self.email], **kwargs)