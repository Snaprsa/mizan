document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('valuationForm');
    const resultsContainer = document.getElementById('resultsContainer');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const closeResults = document.getElementById('closeResults');
    const newValuationBtn = document.getElementById('newValuationBtn');
    const citySelect = document.getElementById('city');
    const propertyTypeSelect = document.getElementById('property_type');
    const districtSelect = document.getElementById('district');

    // Load cities first, then districts
    loadCities();

    // Handle city change - reload districts
    citySelect.addEventListener('change', function () {
        loadDistricts(this.value);
    });

    // Handle property type change (show/hide sections based on type)
    propertyTypeSelect.addEventListener('change', function () {
        if (this.value === 'villa') {
            document.body.classList.remove('land-mode');
            document.body.classList.add('villa-mode');
            // Auto-select certain amenities for villas
            document.getElementById('garden').checked = true;
            document.getElementById('private_entrance').checked = true;
            document.getElementById('elevator').checked = false;
        } else if (this.value === 'land') {
            document.body.classList.remove('villa-mode');
            document.body.classList.add('land-mode');
            // Clear building-related fields for land
            document.getElementById('bedrooms').value = '';
            document.getElementById('bathrooms').value = '';
            document.getElementById('parking_count').value = '';
            document.getElementById('floor_level').value = '';
            document.getElementById('year_built').value = '';
            document.getElementById('finish_tier').value = '';
            document.getElementById('condition_tier').value = '';
        } else {
            document.body.classList.remove('villa-mode');
            document.body.classList.remove('land-mode');
            document.getElementById('garden').checked = false;
            document.getElementById('private_entrance').checked = false;
            document.getElementById('elevator').checked = true;
        }
    });

    // Form submission
    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        // Show loading
        loadingOverlay.classList.add('active');

        const isLand = document.getElementById('property_type').value === 'land';

        // Gather form data
        const formData = {
            city: document.getElementById('city').value,
            property_type: document.getElementById('property_type').value,
            district: document.getElementById('district').value,
            area_sqm: document.getElementById('area_sqm').value,
            year_built: isLand ? null : (document.getElementById('year_built').value || null),
            bedrooms: isLand ? null : (document.getElementById('bedrooms').value || null),
            bathrooms: isLand ? null : (document.getElementById('bathrooms').value || null),
            parking_count: isLand ? null : (document.getElementById('parking_count').value || null),
            floor_level: isLand ? null : (document.getElementById('floor_level').value || null),
            finish_tier: isLand ? null : (document.getElementById('finish_tier').value || null),
            condition_tier: isLand ? null : (document.getElementById('condition_tier').value || null),
            elevator: isLand ? 0 : (document.getElementById('elevator').checked ? 1 : 0),
            central_ac: isLand ? 0 : (document.getElementById('central_ac').checked ? 1 : 0),
            maid_room: isLand ? 0 : (document.getElementById('maid_room').checked ? 1 : 0),
            garden: isLand ? 0 : (document.getElementById('garden').checked ? 1 : 0),
            private_entrance: isLand ? 0 : (document.getElementById('private_entrance').checked ? 1 : 0),
        };

        try {
            const response = await fetch('/api/valuate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            const data = await response.json();

            if (data.success) {
                displayResults(data.valuation);
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to get valuation. Please check if the server is running.');
        } finally {
            loadingOverlay.classList.remove('active');
        }
    });

    // Close results
    closeResults.addEventListener('click', function () {
        resultsContainer.style.display = 'none';
    });

    // New valuation
    newValuationBtn.addEventListener('click', function () {
        resultsContainer.style.display = 'none';
        form.reset();
        document.body.classList.remove('villa-mode');
        document.body.classList.remove('land-mode');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Load cities from API
    async function loadCities() {
        try {
            const response = await fetch('/api/cities');
            const cities = await response.json();

            citySelect.innerHTML = '<option value="">Select city</option>';
            cities.forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                citySelect.appendChild(option);
            });

            // Auto-select first city and load its districts
            if (cities.length > 0) {
                citySelect.value = cities[0];
                loadDistricts(cities[0]);
            }
        } catch (error) {
            console.error('Failed to load cities:', error);
            // Fallback
            const fallbackCities = ["Riyadh"];
            citySelect.innerHTML = '<option value="">Select city</option>';
            fallbackCities.forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                citySelect.appendChild(option);
            });
        }
    }

    // Load districts from API
    async function loadDistricts(city) {
        try {
            const url = city ? `/api/districts?city=${encodeURIComponent(city)}` : '/api/districts';
            const response = await fetch(url);
            const districts = await response.json();

            districtSelect.innerHTML = '<option value="">Select district</option>';
            districts.forEach(district => {
                const option = document.createElement('option');
                option.value = district;
                option.textContent = district;
                districtSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load districts:', error);
            // Fallback districts
            const fallbackDistricts = [
                "Al Olaya", "Al Malqa", "Al Nakheel", "Al Yasmin", "Al Sahafa",
                "Al Muruj", "Hittin", "Al Narjis", "Al Qirawan", "Al Rabwah"
            ];
            districtSelect.innerHTML = '<option value="">Select district</option>';
            fallbackDistricts.forEach(district => {
                const option = document.createElement('option');
                option.value = district;
                option.textContent = district;
                districtSelect.appendChild(option);
            });
        }
    }

    // Display results
    function displayResults(valuation) {
        resultsContainer.style.display = 'block';

        // Scroll to results
        setTimeout(() => {
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);

        // Main value
        document.getElementById('mainValue').textContent = formatSAR(valuation.estimated_value_sar_mid);
        document.getElementById('valueRange').textContent =
            `Range: ${formatSAR(valuation.estimated_value_sar_low)} - ${formatSAR(valuation.estimated_value_sar_high)}`;

        // Metrics
        document.getElementById('pricePerSqm').textContent =
            formatSAR(valuation.estimated_price_per_sqm_mid) + '/sqm';
        document.getElementById('confidenceScore').textContent =
            valuation.confidence_score + '/100';
        document.getElementById('completenessScore').textContent =
            valuation.data_completeness_score + '%';

        // Confidence bar
        const confidence = valuation.confidence_score;
        document.getElementById('confidenceFill').style.width = confidence + '%';
        document.getElementById('confidenceLabel').textContent = getConfidenceLabel(confidence);

        // Value drivers
        const driversList = document.getElementById('driversList');
        driversList.innerHTML = '';
        if (valuation.explanation && valuation.explanation.top_drivers) {
            valuation.explanation.top_drivers.forEach(driver => {
                const tag = document.createElement('span');
                tag.className = 'driver-tag';
                tag.textContent = driver;
                driversList.appendChild(tag);
            });
        }

        // Segment info
        const segmentInfo = document.getElementById('segmentInfo');
        if (valuation.explanation && valuation.explanation.segment) {
            const seg = valuation.explanation.segment;
            segmentInfo.innerHTML = `
                <strong>Market Segment:</strong> ${seg.key}<br>
                <strong>Comparables:</strong> ${seg.count} properties | 
                <strong>Market Range:</strong> ${formatSAR(seg.p10)} - ${formatSAR(seg.p90)}/sqm
            `;
        }

        // Show comparables section and fetch deals
        const comparablesSection = document.getElementById('comparablesSection');
        const showComparablesToggle = document.getElementById('showComparables');
        const comparablesList = document.getElementById('comparablesList');

        comparablesSection.style.display = 'block';
        showComparablesToggle.checked = false;
        comparablesList.style.display = 'none';
        comparablesList.innerHTML = '';

        // Fetch comparable deals
        const propertyType = document.getElementById('property_type').value;
        const areaSqm = document.getElementById('area_sqm').value;
        const district = document.getElementById('district').value;

        fetchComparables(propertyType, areaSqm, district);

        // Toggle handler
        showComparablesToggle.onchange = function () {
            comparablesList.style.display = this.checked ? 'block' : 'none';
        };
    }

    // Fetch comparable deals from API
    async function fetchComparables(propertyType, areaSqm, district) {
        const comparablesList = document.getElementById('comparablesList');

        try {
            const response = await fetch('/api/comparables', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    property_type: propertyType,
                    area_sqm: areaSqm,
                    district: district,
                    limit: 5
                }),
            });

            const data = await response.json();

            if (data.success && data.comparables.length > 0) {
                comparablesList.innerHTML = `
                    <p class="comparables-intro">Found ${data.count} similar ${propertyType}s near ${areaSqm} sqm:</p>
                    <div class="comparables-cards">
                        ${data.comparables.map(comp => `
                            <div class="comparable-card">
                                <div class="comp-header">
                                    <span class="comp-district">${comp.district}</span>
                                    <span class="comp-date">${comp.trans_date || 'Recent'}</span>
                                </div>
                                <div class="comp-price">${formatSAR(comp.total_price_sar)}</div>
                                <div class="comp-details">
                                    <span>📐 ${comp.area_sqm} sqm</span>
                                    <span>💰 ${formatSAR(comp.price_per_sqm)}/sqm</span>
                                </div>
                                <div class="comp-features">
                                    ${comp.bedrooms ? `<span>🛏️ ${comp.bedrooms} bed</span>` : ''}
                                    ${comp.bathrooms ? `<span>🚿 ${comp.bathrooms} bath</span>` : ''}
                                    ${comp.year_built ? `<span>📅 Built ${comp.year_built}</span>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            } else {
                comparablesList.innerHTML = '<p class="no-comparables">No comparable deals found in the database.</p>';
            }
        } catch (error) {
            console.error('Failed to fetch comparables:', error);
            comparablesList.innerHTML = '<p class="no-comparables">Could not load comparable deals.</p>';
        }
    }

    // Format SAR currency
    function formatSAR(value) {
        if (value >= 1000000) {
            return (value / 1000000).toFixed(2) + 'M SAR';
        } else if (value >= 1000) {
            return (value / 1000).toFixed(0) + 'K SAR';
        }
        return value.toLocaleString() + ' SAR';
    }

    // Get confidence label
    function getConfidenceLabel(score) {
        if (score >= 90) return 'Very High';
        if (score >= 75) return 'High';
        if (score >= 60) return 'Moderate';
        if (score >= 40) return 'Low';
        return 'Very Low';
    }
});
