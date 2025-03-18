from django.db import models


class FlowFile(models.Model):
    filename = models.CharField(max_length=255, unique=True)  # Tracks D0010 file linked to a meter reading
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename}"


class MeterReading(models.Model):
    mpan_core = models.IntegerField(db_index=True)  # J0003: Searchable MPAN
    meter_serial_number = models.CharField(max_length=10, db_index=True)  # J0004: Searchable Meter ID
    reading_date = models.DateTimeField()  # J0016: Stores the reading timestamp
    register_reading = models.DecimalField(max_digits=10, decimal_places=1)  # J0040: Stores the actual reading value
    flow_file = models.ForeignKey(FlowFile, on_delete=models.CASCADE)  # Links to source file, modeling a one to many relationship between flow files and readings

    def __str__(self):
        return f"MPAN: {self.mpan_core} | SERIAL: {self.meter_serial_number}"
