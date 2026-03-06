"""
Tests for core/csv_loader.py — load_csv and CSVValidationError.
"""
import pytest
from pathlib import Path

from core.csv_loader import load_csv, CSVValidationError


# ── Helpers ───────────────────────────────────────────────────────────────────

def write_csv(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "registers.csv"
    p.write_text(content)
    return p


VALID_CSV = """\
address,type,name,value,access
1,holding,pump_speed,0,RW
2,holding,setpoint_temp,200,RW
3,input,inlet_pressure,0,R
4,coil,pump_enable,0,RW
5,discrete,fault_active,0,R
"""


# ── Happy path ────────────────────────────────────────────────────────────────

class TestValidCSV:
    def test_returns_correct_count(self, tmp_path):
        regs = load_csv(write_csv(tmp_path, VALID_CSV))
        assert len(regs) == 5

    def test_holding_register_parsed(self, tmp_path):
        regs = load_csv(write_csv(tmp_path, VALID_CSV))
        r = next(r for r in regs if r.address == 1)
        assert r.reg_type == "holding"
        assert r.name == "pump_speed"
        assert r.value == 0
        assert r.writable is True

    def test_read_only_register(self, tmp_path):
        regs = load_csv(write_csv(tmp_path, VALID_CSV))
        r = next(r for r in regs if r.address == 3)
        assert r.writable is False

    def test_all_register_types_accepted(self, tmp_path):
        csv = "address,type,name,value,access\n1,holding,a,0,R\n2,input,b,0,R\n3,coil,c,0,R\n4,discrete,d,0,R\n"
        regs = load_csv(write_csv(tmp_path, csv))
        types = {r.reg_type for r in regs}
        assert types == {"holding", "input", "coil", "discrete"}

    def test_type_is_lowercased(self, tmp_path):
        csv = "address,type,name,value,access\n1,HOLDING,speed,0,RW\n"
        regs = load_csv(write_csv(tmp_path, csv))
        assert regs[0].reg_type == "holding"

    def test_access_rw_case_insensitive(self, tmp_path):
        csv = "address,type,name,value,access\n1,holding,a,0,rw\n"
        regs = load_csv(write_csv(tmp_path, csv))
        assert regs[0].writable is True

    def test_value_true_string(self, tmp_path):
        csv = "address,type,name,value,access\n1,coil,enable,true,RW\n"
        regs = load_csv(write_csv(tmp_path, csv))
        assert regs[0].value == 1

    def test_value_false_string(self, tmp_path):
        csv = "address,type,name,value,access\n1,coil,enable,false,RW\n"
        regs = load_csv(write_csv(tmp_path, csv))
        assert regs[0].value == 0

    def test_whitespace_stripped_from_columns(self, tmp_path):
        csv = " address , type , name , value , access \n1,holding,speed,0,RW\n"
        regs = load_csv(write_csv(tmp_path, csv))
        assert len(regs) == 1

    def test_whitespace_stripped_from_values(self, tmp_path):
        csv = "address,type,name,value,access\n 1 , holding , pump speed , 0 , RW \n"
        regs = load_csv(write_csv(tmp_path, csv))
        assert regs[0].name == "pump speed"
        assert regs[0].address == 1


# ── File errors ───────────────────────────────────────────────────────────────

class TestFileErrors:
    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_csv(tmp_path / "nonexistent.csv")


# ── Column validation ─────────────────────────────────────────────────────────

class TestMissingColumns:
    def test_missing_address_column(self, tmp_path):
        csv = "type,name,value,access\nholding,speed,0,RW\n"
        with pytest.raises(CSVValidationError, match="missing required columns"):
            load_csv(write_csv(tmp_path, csv))

    def test_missing_type_column(self, tmp_path):
        csv = "address,name,value,access\n1,speed,0,RW\n"
        with pytest.raises(CSVValidationError, match="missing required columns"):
            load_csv(write_csv(tmp_path, csv))

    def test_missing_multiple_columns(self, tmp_path):
        csv = "address,name\n1,speed\n"
        with pytest.raises(CSVValidationError, match="missing required columns"):
            load_csv(write_csv(tmp_path, csv))


# ── Row-level validation ──────────────────────────────────────────────────────

class TestRowValidation:
    def test_invalid_address(self, tmp_path):
        csv = "address,type,name,value,access\nabc,holding,speed,0,RW\n"
        with pytest.raises(CSVValidationError, match="'address' must be an integer"):
            load_csv(write_csv(tmp_path, csv))

    def test_duplicate_address(self, tmp_path):
        csv = "address,type,name,value,access\n1,holding,a,0,RW\n1,holding,b,0,RW\n"
        with pytest.raises(CSVValidationError, match="Duplicate address"):
            load_csv(write_csv(tmp_path, csv))

    def test_invalid_type(self, tmp_path):
        csv = "address,type,name,value,access\n1,relay,speed,0,RW\n"
        with pytest.raises(CSVValidationError, match="'type' must be one of"):
            load_csv(write_csv(tmp_path, csv))

    def test_empty_name(self, tmp_path):
        csv = "address,type,name,value,access\n1,holding,,0,RW\n"
        with pytest.raises(CSVValidationError, match="'name' cannot be empty"):
            load_csv(write_csv(tmp_path, csv))

    def test_invalid_value(self, tmp_path):
        csv = "address,type,name,value,access\n1,holding,speed,abc,RW\n"
        with pytest.raises(CSVValidationError, match="'value' must be numeric"):
            load_csv(write_csv(tmp_path, csv))

    def test_invalid_access(self, tmp_path):
        csv = "address,type,name,value,access\n1,holding,speed,0,X\n"
        with pytest.raises(CSVValidationError, match="'access' must be R or RW"):
            load_csv(write_csv(tmp_path, csv))

    def test_empty_file_body(self, tmp_path):
        csv = "address,type,name,value,access\n"
        with pytest.raises(CSVValidationError, match="no register rows"):
            load_csv(write_csv(tmp_path, csv))
