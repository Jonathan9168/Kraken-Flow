from django.contrib import admin
from .models import FlowFile, MeterReading


class FlowFileAdmin(admin.ModelAdmin):
    search_fields = ['filename']
    list_display = ('filename', 'uploaded_at')


admin.site.register(FlowFile, FlowFileAdmin)


class MeterReadingAdmin(admin.ModelAdmin):
    search_fields = ['mpan_core', 'meter_serial_number']
    list_display = ('mpan_core', 'meter_serial_number', 'reading_date', 'register_reading', 'flow_file')
    list_filter = ['mpan_core', 'meter_serial_number']


admin.site.register(MeterReading, MeterReadingAdmin)
