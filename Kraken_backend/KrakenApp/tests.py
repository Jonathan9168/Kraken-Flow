import os
import tempfile
from datetime import datetime
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from .models import FlowFile, MeterReading


class LoadD0010CommandTest(TestCase):
    """Unit tests for load_d0010 management command"""

    def setUp(self):
        """Set up a temporary directory and test .uff files"""
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_file = os.path.join(self.test_dir.name, "test_d0010.uff")

        # Create a sample .uff file
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("026|1200033197420|V|\n")
            f.write("028|L85A 28596|C|\n")
            f.write("030|S|20160226000000|17393.0|||T|N|\n")

    def tearDown(self):
        """Clean up the temporary directory"""
        self.test_dir.cleanup()

    def test_load_d0010_valid_file(self):
        """Test loading a valid .uff file"""
        call_command("load_d0010", self.test_file)

        # Check if the file was processed
        self.assertTrue(FlowFile.objects.filter(filename="test_d0010.uff").exists())

        # Check if the meter reading was saved
        self.assertEqual(MeterReading.objects.count(), 1)
        reading = MeterReading.objects.first()
        self.assertEqual(reading.mpan_core, 1200033197420)
        self.assertEqual(reading.meter_serial_number, "L85A 28596")
        self.assertEqual(reading.register_reading, 17393.0)

    def test_load_d0010_duplicate_file(self):
        """Test that a duplicate file is skipped"""
        call_command("load_d0010", self.test_file)
        call_command("load_d0010", self.test_file)

        self.assertEqual(FlowFile.objects.count(), 1)
        self.assertEqual(MeterReading.objects.count(), 1)

    def test_load_d0010_directory(self):
        """Test loading multiple files from a directory"""
        second_file = os.path.join(self.test_dir.name, "test_d0010_2.uff")
        with open(second_file, "w", encoding="utf-8") as f:
            f.write("026|1200033197420|V|\n")
            f.write("028|L85A 28596|C|\n")
            f.write("030|S|20160226000000|17393.0|||T|N|\n")

        call_command("load_d0010", self.test_dir.name)

        # Check both files were processed
        self.assertEqual(FlowFile.objects.count(), 2)
        self.assertEqual(MeterReading.objects.count(), 2)

    def test_load_d0010_empty_directory(self):
        """Test behavior when a directory has no .uff files"""
        empty_dir = tempfile.TemporaryDirectory()
        call_command("load_d0010", empty_dir.name)
        self.assertEqual(FlowFile.objects.count(), 0)
        empty_dir.cleanup()

    def test_load_d0010_missing_file(self):
        """Test handling a missing file"""
        missing_file = os.path.join(self.test_dir.name, "missing.uff")
        with self.assertRaises(CommandError):
            call_command("load_d0010", missing_file)

    def test_load_d0010_corrupt_data(self):
        """Test handling of corrupt .uff file"""
        corrupt_file = os.path.join(self.test_dir.name, "corrupt.uff")
        with open(corrupt_file, "w", encoding="utf-8") as f:
            f.write("026|1234567890123\n")
            f.write("028|TEST123456\n")
            f.write("030|INVALID_DATE|100.5\n")  # Corrupt date format

        call_command("load_d0010", corrupt_file)

        # The file should be recorded, but no readings should be saved
        self.assertTrue(FlowFile.objects.filter(filename="corrupt.uff").exists())
        self.assertEqual(MeterReading.objects.count(), 0)


class FlowFileModelTest(TestCase):
    """Unit tests for FlowFile model"""

    def test_str_representation(self):
        """Test __str__ method"""
        flow_file = FlowFile.objects.create(filename="test_file.uff")
        self.assertEqual(str(flow_file), "test_file.uff")


class MeterReadingModelTest(TestCase):
    """Unit tests for MeterReading model"""

    def test_str_representation(self):
        """Test __str__ method"""
        flow_file = FlowFile.objects.create(filename="test_file.uff")
        reading = MeterReading.objects.create(
            mpan_core=1234567890123,
            meter_serial_number="METER123",
            reading_date=datetime(2024, 3, 17, 23, 59, 59),
            register_reading=50.5,
            flow_file=flow_file,
        )
        self.assertEqual(str(reading), "MPAN: 1234567890123 | SERIAL: METER123")
