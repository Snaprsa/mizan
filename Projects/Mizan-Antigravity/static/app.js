// Mizan Web UI - JavaScript Logic

// Field weights for completeness calculation
const FIELD_WEIGHTS = {
    area_sqm: 1.0,
    property_type: 1.0,
    city: 1.0,
    district: 0.8,
    bedrooms: 0.6,
    bathrooms: 0.5,
    year_built: 0.7,
    finish_tier: 0.4,
    condition_tier: 0.4,
    parking_count: 0.3,
    floor_level: 0.3,
    elevator: 0.2,
    central_ac: 0.2,
    maid_room: 0.2,
    garden: 0.2,
    private_entrance: 0.2,
};

// Toggle section visibility
function toggleSection(sectionId) {
    const section = document.getElementById(`section-${sectionId}`);
    section.classList.toggle('open');
}

// Calculate and update completeness
function updateCompleteness() {
    const form = document.getElementById('valuation-form');
    const formData = new FormData(form);

    let filledWeight = 0;
    let totalWeight = 0;
    let filledCount = 0;

    for (const [field, weight] of Object.entries(FIELD_WEIGHTS)) {
        totalWeight += weight;

        const value = formData.get(field);
        if (value && value.trim() !== '') {
            filledWeight += weight;
            filledCount++;
        }
    }

    const percentage = Math.round((filledWeight / totalWeight) * 100);

    // Update UI
    document.getElementById('completeness-count').textContent = `${filledCount} / ${Object.keys(FIELD_WEIGHTS).length}`;
    document.getElementById('progress-fill').style.width = `${percentage}%`;
}

// Format number with commas (Arabic style)
function formatNumber(num) {
    return new Intl.NumberFormat('ar-SA').format(Math.round(num));
}

// Format currency
function formatCurrency(num) {
    return formatNumber(num);
}

// Handle form submission
async function handleSubmit(event) {
    event.preventDefault();

    const form = document.getElementById('valuation-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');

    // Validate required fields
    const area = form.area_sqm.value;
    const city = form.city.value;
    const district = form.district.value;
    const propertyType = form.property_type.value;

    if (!area || !city || !district || !propertyType) {
        alert('يرجى إدخال جميع الحقول المطلوبة');
        return;
    }

    // Show loading state
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    btnText.textContent = 'جارٍ التحليل...';

    try {
        // Collect form data
        const formData = new FormData(form);
        const data = {};

        for (const [key, value] of formData.entries()) {
            if (value && value.trim() !== '') {
                data[key] = value;
            }
        }

        // Handle checkboxes (they only appear if checked)
        const checkboxes = ['elevator', 'central_ac', 'maid_room', 'garden', 'private_entrance'];
        for (const checkbox of checkboxes) {
            const input = form.querySelector(`input[name="${checkbox}"]`);
            data[checkbox] = input && input.checked ? 1 : 0;
        }

        // Make API call
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'حدث خطأ في التقييم');
        }

        // Display results
        displayResults(result);

    } catch (error) {
        console.error('Error:', error);
        alert('حدث خطأ: ' + error.message);
    } finally {
        // Reset button
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        btnText.textContent = 'احسب القيمة التقديرية';
    }
}

// Display results
function displayResults(result) {
    // Show results section
    const resultsSection = document.getElementById('results-section');
    resultsSection.style.display = 'block';

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Update values
    document.getElementById('value-mid').textContent = formatCurrency(result.estimated_value_sar_mid);
    document.getElementById('value-low').textContent = formatCurrency(result.estimated_value_sar_low);
    document.getElementById('value-high').textContent = formatCurrency(result.estimated_value_sar_high);
    document.getElementById('price-per-sqm').textContent = formatCurrency(result.estimated_price_per_sqm_mid);

    // Update scores
    const confidence = result.confidence_score;
    const completeness = result.data_completeness_score;

    document.getElementById('confidence-score').textContent = confidence;
    document.getElementById('confidence-display').textContent = confidence;
    document.getElementById('completeness-display').textContent = completeness;

    // Animate score bars
    setTimeout(() => {
        document.getElementById('confidence-fill').style.width = `${confidence}%`;
        document.getElementById('completeness-fill').style.width = `${completeness}%`;
    }, 100);

    // Display comparable deals
    displayComparableDeals(result.comparable_deals || []);
}

// Display comparable deals
function displayComparableDeals(deals) {
    const compsSection = document.getElementById('comps-section');
    const compsList = document.getElementById('comps-list');
    const compsCount = document.getElementById('comps-count');

    if (!deals || deals.length === 0) {
        compsSection.style.display = 'none';
        return;
    }

    compsSection.style.display = 'block';
    compsCount.textContent = deals.length;

    // Clear existing
    compsList.innerHTML = '';

    // Add each deal
    deals.forEach(deal => {
        const card = document.createElement('div');
        card.className = `comp-card${deal.same_district ? ' same-district' : ''}`;

        card.innerHTML = `
            <div class="comp-info">
                <span class="comp-district">${deal.district}${deal.same_district ? ' ✓' : ''}</span>
                <span class="comp-details">${deal.area_sqm} م² • ${deal.trans_date}</span>
            </div>
            <div class="comp-price">
                <div class="comp-total">${formatNumber(deal.total_price)} ر.س</div>
                <div class="comp-sqm">${formatNumber(deal.price_per_sqm)} ر.س/م²</div>
            </div>
        `;

        compsList.appendChild(card);
    });
}

// Reset form
function resetForm() {
    const form = document.getElementById('valuation-form');
    form.reset();

    // Hide results
    document.getElementById('results-section').style.display = 'none';

    // Reset completeness
    updateCompleteness();

    // Reset score bars
    document.getElementById('confidence-fill').style.width = '0%';
    document.getElementById('completeness-fill').style.width = '0%';

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Store districts data for price range lookup
let districtsData = {};

// Load districts for selected city
async function loadDistricts(city) {
    const districtSelect = document.getElementById('district');
    const districtInfo = document.getElementById('district-info');

    if (!city) {
        districtSelect.innerHTML = '<option value="">اختر المدينة أولاً</option>';
        districtInfo.textContent = '';
        return;
    }

    districtSelect.innerHTML = '<option value="">جارٍ التحميل...</option>';
    districtInfo.textContent = '';

    try {
        const response = await fetch(`/api/districts/${encodeURIComponent(city)}`);
        const data = await response.json();

        if (data.districts && data.districts.length > 0) {
            // Store for later lookup
            districtsData = {};
            data.districts.forEach(d => {
                districtsData[d.name] = d;
            });

            // Populate dropdown
            districtSelect.innerHTML = '<option value="">اختر الحي</option>';
            data.districts.forEach(d => {
                const option = document.createElement('option');
                option.value = d.name;
                option.textContent = `${d.name} (${d.count} صفقة)`;
                districtSelect.appendChild(option);
            });
        } else {
            districtSelect.innerHTML = '<option value="">لا توجد أحياء - أدخل الحي يدوياً</option>';
            // Fallback to text input behavior
        }
    } catch (error) {
        console.error('Error loading districts:', error);
        districtSelect.innerHTML = '<option value="">خطأ في التحميل</option>';
    }

    updateCompleteness();
}

// Show district price range info
function showDistrictInfo(districtName) {
    const districtInfo = document.getElementById('district-info');

    if (districtName && districtsData[districtName]) {
        const d = districtsData[districtName];
        districtInfo.textContent = `💰 متوسط السعر: ${formatNumber(d.avg_price_sqm)} ر.س/م² | المدى: ${formatNumber(d.min_price_sqm)} - ${formatNumber(d.max_price_sqm)}`;
    } else {
        districtInfo.textContent = '';
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('valuation-form');
    const citySelect = document.getElementById('city');
    const districtSelect = document.getElementById('district');

    // Add submit handler
    form.addEventListener('submit', handleSubmit);

    // Add change listeners for completeness
    form.addEventListener('change', updateCompleteness);
    form.addEventListener('input', updateCompleteness);

    // Load districts when city changes
    citySelect.addEventListener('change', (e) => {
        loadDistricts(e.target.value);
    });

    // Show district info when district changes
    districtSelect.addEventListener('change', (e) => {
        showDistrictInfo(e.target.value);
        updateCompleteness();
    });

    // Initial completeness calculation
    updateCompleteness();

    // Load districts for initially selected city (if any)
    if (citySelect.value) {
        loadDistricts(citySelect.value);
    }
});
