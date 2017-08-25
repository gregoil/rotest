"""Define the Django administrator web interface for Rotest core.

Used in order to modify the appearance of tables in the admin site.
"""
# pylint: disable=too-many-public-methods
from django.contrib import admin

from rotest.core.models import RunData, SuiteData, CaseData, SignatureData


class TestDataAdmin(admin.ModelAdmin):
    """Basic ModelAdmin for all :class:`rotest.GeneralData` models."""
    list_display = ['name', 'success', 'status', 'start_time', 'end_time']
    ordering = ['-start_time']


class TestDataInline(admin.TabularInline):
    """Basic TabularInline for all :class:`rotest.GeneralData` sub-models."""
    extra = 0
    fk_name = 'parent'
    can_delete = False
    fields = ['admin_link', 'status', 'start_time', 'end_time', 'success']
    readonly_fields = fields


class CaseDataAdmin(TestDataAdmin):
    """ModelAdmin for :class:`rotest.core.models.CaseData` model.

    Note:
        Resources list is set as "readonly" because of display issues.
    """
    list_display = TestDataAdmin.list_display + ['parent_link',
                                                 'exception_type',
                                                 'resources_names']
    fields = ['name', 'success', 'status', 'start_time', 'end_time',
              'exception_type', 'traceback', 'resources']
    readonly_fields = ['resources']


class SignatureDataAdmin(admin.ModelAdmin):
    """ModelAdmin for :class:`rotest.core.models.SignatureData` model."""
    fields = ['name', 'link', 'pattern']


class CaseInline(TestDataInline):
    """TabularInline for :class:`rotest.core.models.CaseData` model."""
    model = CaseData
    fields = TestDataInline.fields + ['exception_type']
    readonly_fields = fields


class SuiteInline(TestDataInline):
    """TabularInline for :class:`rotest.SuiteData` model."""
    model = SuiteData


class SuiteDataAdmin(TestDataAdmin):
    """ModelAdmin for :class:`rotest.SuiteData` model."""
    inlines = [SuiteInline]
    fields = TestDataAdmin.list_display
    list_display = TestDataAdmin.list_display + ['parent_link',
                                                 'children_link']


class RunDataAdmin(admin.ModelAdmin):
    """ModelAdmin for :class:`rotest.RunData` model."""
    list_display = ['main_test', 'run_name', 'user_name', 'artifact_path',
                    'main_test_link']


# Register the Models & corresponding AdminModels to Django admin site
admin.site.register(SignatureData, SignatureDataAdmin)
admin.site.register(SuiteData, SuiteDataAdmin)
admin.site.register(CaseData, CaseDataAdmin)
admin.site.register(RunData, RunDataAdmin)
