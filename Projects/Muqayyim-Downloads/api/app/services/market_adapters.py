"""Providers normalize to ObservationInput; no provider-specific database columns."""
import csv
import io
from typing import Protocol
from pydantic import ValidationError
from api.app.schemas.foundation import ObservationInput


class MarketAdapter(Protocol):
    def normalize(self, payload: str) -> list[ObservationInput]: ...


class CsvObservationAdapter:
    """Strict canonical CSV import. Raw/normalized values and units are explicit, never inferred."""
    required = {'external_id', 'observed_on', 'city', 'property_type', 'metric', 'unit', 'raw_value', 'normalized_value', 'reliability'}

    def normalize(self, payload):
        reader = csv.DictReader(io.StringIO(payload.lstrip('\ufeff')))
        if not self.required.issubset(reader.fieldnames or []):
            raise ValueError('CSV requires columns: ' + ', '.join(sorted(self.required)))
        rows = []
        for line, values in enumerate(reader, 2):
            if len(rows) >= 1000:
                raise ValueError('Maximum 1000 observations per import')
            if None in values:
                raise ValueError(f'CSV row {line}: extra columns')
            allowed = self.required | {'country', 'district'}
            if set(values) - allowed:
                raise ValueError('Unsupported CSV columns: ' + ', '.join(sorted(set(values) - allowed)))
            values = {k: v for k, v in values.items() if v != ''}
            values['metadata'] = {'import_format': 'canonical_csv_v1', 'row': line}
            try:
                rows.append(ObservationInput.model_validate(values))
            except ValidationError as exc:
                raise ValueError(f'CSV row {line}: {exc}') from exc
        if not rows:
            raise ValueError('CSV contains no observations')
        return rows
