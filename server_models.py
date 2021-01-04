 # python -m pwiz postgresql -H lab -p 5432 -u postgres -P 123 lab > server_models.py
from peewee import *
from playhouse.postgres_ext import *

database = PostgresqlDatabase('lab', **{'host': 'lab', 'port': 5432, 'user': 'postgres', 'password': '123'})

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

class Ap(BaseModel):
    adapter = CharField()
    admin_id = CharField(null=True)
    admin_pw = CharField(null=True)
    chip1 = CharField(null=True)
    chip1_protocols = CharField(null=True)
    chip2 = CharField(null=True)
    chip2_protocols = CharField(null=True)
    cpu = CharField(null=True)
    cycle = CharField(null=True)
    fw = CharField(null=True)
    id = BigAutoField()
    is_active = BooleanField()
    is_scrap = BooleanField()
    name = CharField()
    network_technology_standard = CharField(null=True)
    no = CharField()
    remark = TextField(null=True)
    ssid_2d4 = CharField()
    ssid_2d4_band = CharField(null=True)
    ssid_2d4_bssid = CharField(null=True)
    ssid_2d4_password = CharField()
    ssid_5 = CharField(null=True)
    ssid_5_band = CharField(null=True)
    ssid_5_bssid = CharField(null=True)
    ssid_5_password = CharField(null=True)
    status = CharField()
    storage = CharField()
    vender = CharField(null=True)

    class Meta:
        table_name = 'ap'

class AuthUser(BaseModel):
    date_joined = DateTimeField()
    email = CharField()
    first_name = CharField()
    is_active = BooleanField()
    is_staff = BooleanField()
    is_superuser = BooleanField()
    last_login = DateTimeField(null=True)
    last_name = CharField()
    password = CharField()
    username = CharField(index=True)

    class Meta:
        table_name = 'auth_user'

class Member(BaseModel):
    user = ForeignKeyField(column_name='user_id', field='id', model=AuthUser, unique=True)
    usernameincompany = CharField()

    class Meta:
        table_name = 'member'

class ApBorrowHistory(BaseModel):
    ap = ForeignKeyField(column_name='ap_id', field='id', model=Ap)
    back_time = TimeField(null=True)
    borrower = ForeignKeyField(column_name='borrower_id', field='id', model=Member)
    id = BigAutoField()
    rent_time = DateTimeField()

    class Meta:
        table_name = 'ap_borrow_history'

class AuthGroup(BaseModel):
    name = CharField(index=True)

    class Meta:
        table_name = 'auth_group'

class DjangoContentType(BaseModel):
    app_label = CharField()
    model = CharField()

    class Meta:
        table_name = 'django_content_type'
        indexes = (
            (('app_label', 'model'), True),
        )

class AuthPermission(BaseModel):
    codename = CharField()
    content_type = ForeignKeyField(column_name='content_type_id', field='id', model=DjangoContentType)
    name = CharField()

    class Meta:
        table_name = 'auth_permission'
        indexes = (
            (('content_type', 'codename'), True),
        )

class AuthGroupPermissions(BaseModel):
    group = ForeignKeyField(column_name='group_id', field='id', model=AuthGroup)
    permission = ForeignKeyField(column_name='permission_id', field='id', model=AuthPermission)

    class Meta:
        table_name = 'auth_group_permissions'
        indexes = (
            (('group', 'permission'), True),
        )

class AuthUserGroups(BaseModel):
    group = ForeignKeyField(column_name='group_id', field='id', model=AuthGroup)
    user = ForeignKeyField(column_name='user_id', field='id', model=AuthUser)

    class Meta:
        table_name = 'auth_user_groups'
        indexes = (
            (('user', 'group'), True),
        )

class AuthUserUserPermissions(BaseModel):
    permission = ForeignKeyField(column_name='permission_id', field='id', model=AuthPermission)
    user = ForeignKeyField(column_name='user_id', field='id', model=AuthUser)

    class Meta:
        table_name = 'auth_user_user_permissions'
        indexes = (
            (('user', 'permission'), True),
        )

class DjangoAdminLog(BaseModel):
    action_flag = SmallIntegerField()
    action_time = DateTimeField()
    change_message = TextField()
    content_type = ForeignKeyField(column_name='content_type_id', field='id', model=DjangoContentType, null=True)
    object_id = TextField(null=True)
    object_repr = CharField()
    user = ForeignKeyField(column_name='user_id', field='id', model=AuthUser)

    class Meta:
        table_name = 'django_admin_log'

class DjangoMigrations(BaseModel):
    app = CharField()
    applied = DateTimeField()
    name = CharField()

    class Meta:
        table_name = 'django_migrations'

class DjangoSession(BaseModel):
    expire_date = DateTimeField(index=True)
    session_data = TextField()
    session_key = CharField(primary_key=True)

    class Meta:
        table_name = 'django_session'

class Driver(BaseModel):
    category = CharField(null=True)
    id = BigAutoField()
    name = CharField(null=True)
    owner = ForeignKeyField(column_name='owner_id', field='id', model=Member)
    package_name = TextField(index=True, null=True)
    path = CharField(null=True)
    release_time = TimeField()
    version = CharField()

    class Meta:
        table_name = 'driver'

class Module(BaseModel):
    category = CharField(null=True)
    deliverable_name = TextField(null=True)
    device_id = CharField(null=True)
    id = BigAutoField()
    owner = ForeignKeyField(column_name='owner_id', field='id', model=Member)
    short_name = CharField()
    subsys_device_id = CharField(null=True)
    subsys_vender_id = CharField(null=True)
    support_driver = ArrayField(field_class=BigIntegerField, null=True)
    vender_id = CharField(null=True)

    class Meta:
        table_name = 'module'

class Platform(BaseModel):
    behavior = CharField(null=True)
    chipset = CharField(null=True)
    codename = CharField(null=True)
    content = CharField(null=True)
    cycle = CharField(null=True)
    development_center = CharField(null=True)
    forecast_cycle = CharField(null=True)
    forecast_series = CharField(null=True)
    group = CharField(null=True)
    id = BigAutoField()
    marketing_name = CharField(null=True)
    odm = CharField(null=True)
    pdm = CharField(null=True)
    sepm = CharField(null=True)
    series = CharField(null=True)
    target = CharField(null=True)
    update_time = DateTimeField()

    class Meta:
        table_name = 'platform'

class PlatformConfig(BaseModel):
    config_name = CharField()
    config_url = CharField()
    id = BigAutoField()

    class Meta:
        table_name = 'platform_config'

class UutPhase(BaseModel):
    id = BigAutoField()
    phase_text = CharField(index=True, null=True)

    class Meta:
        table_name = 'uut_phase'

class PlatformPhase(BaseModel):
    config = ForeignKeyField(column_name='config_id', field='id', model=PlatformConfig, null=True)
    phase = ForeignKeyField(column_name='phase_id', field='id', model=UutPhase)
    platform = ForeignKeyField(column_name='platform_id', field='id', model=Platform)

    class Meta:
        table_name = 'platform_phase'
        indexes = (
            (('platform', 'phase'), True),
        )

class Tool(BaseModel):
    id = BigAutoField()
    name = CharField()
    path = CharField(null=True)
    version = CharField(null=True)

    class Meta:
        table_name = 'tool'

class Script(BaseModel):
    bt = BooleanField()
    create_time = DateTimeField()
    id = BigAutoField()
    lan = BooleanField()
    name = TextField(index=True)
    nfc = BooleanField()
    path = CharField(null=True)
    rfid = BooleanField()
    tool = ForeignKeyField(column_name='tool_id', field='id', model=Tool, null=True)
    version = CharField(null=True)
    wlan = BooleanField()
    wwan = BooleanField()

    class Meta:
        table_name = 'script'

class UutStatus(BaseModel):
    id = BigAutoField()
    status_text = CharField(index=True, null=True)

    class Meta:
        table_name = 'uut_status'

class Uut(BaseModel):
    cpu = CharField(null=True)
    id = BigAutoField()
    keyin_time = DateTimeField()
    platform_phase = ForeignKeyField(column_name='platform_phase_id', field='id', model=PlatformPhase, null=True)
    position = CharField(null=True)
    remark = TextField(null=True)
    scrap = BooleanField()
    scrap_reason = TextField(null=True)
    sku = CharField(null=True)
    sn = CharField(index=True)
    status = ForeignKeyField(column_name='status_id', field='id', model=UutStatus, null=True)

    class Meta:
        table_name = 'uut'

class UutBorrowHistory(BaseModel):
    back_time = DateTimeField(null=True)
    id = BigAutoField()
    member = ForeignKeyField(column_name='member_id', field='id', model=Member, null=True)
    purpose = TextField(null=True)
    rent_time = DateTimeField()
    uut = ForeignKeyField(column_name='uut_id', field='id', model=Uut)

    class Meta:
        table_name = 'uut_borrow_history'

