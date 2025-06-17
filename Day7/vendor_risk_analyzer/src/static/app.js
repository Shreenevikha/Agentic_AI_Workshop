document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('analyzeForm');
    const fileInput = document.getElementById('files');
    const resultsDiv = document.getElementById('results');
    const loading = document.getElementById('loading');
    const resultsContent = document.getElementById('resultsContent');
    const riskScoreSection = document.getElementById('riskScoreSection');
    const scoreValue = document.getElementById('scoreValue');
    const riskFactorsList = document.getElementById('riskFactors');

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        resultsDiv.classList.add('hidden');
        loading.classList.remove('hidden');
        resultsContent.innerHTML = '';
        riskScoreSection.classList.add('hidden'); // Hide risk section initially

        const formData = new FormData();
        formData.append('vendor_name', document.getElementById('vendorName').value);
        formData.append('gstin', document.getElementById('gstin').value);
        
        const files = fileInput.files;
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! Status: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            loading.classList.add('hidden');
            renderResults(data);
            resultsDiv.classList.remove('hidden');
        } catch (err) {
            loading.classList.add('hidden');
            resultsContent.innerHTML = `<div class="card"><span style="color:red;">Error analyzing documents: ${err.message}</span></div>`;
            resultsDiv.classList.remove('hidden');
        }
    });

    function renderResults(data) {
        let html = '';
        
        // Vendor Info
        html += `<div class="card result-section"><h3>Vendor Information</h3>
            <p><b>Name:</b> ${data.vendor_info.name}</p>
            <p><b>GSTIN:</b> ${data.vendor_info.gstin}</p>
            <p><b>Analysis Date:</b> ${new Date(data.vendor_info.analysis_date).toLocaleString()}</p>
        </div>`;
        
        // Document Analysis
        html += `<div class="card result-section"><h3>Document Analysis</h3>
            <p><b>Total Documents Processed:</b> ${data.document_analysis.total_documents}</p>`;
        data.document_analysis.processed_documents.forEach((doc, idx) => {
            html += `<div style="margin-top:15px; border-top: 1px solid #eee; padding-top: 10px;">
                <h4>Document ${idx+1}: ${doc.metadata.filename}</h4>
                <p><b>File Size:</b> ${Math.round(doc.metadata.file_size / 1024)} KB</p>
                <p><b>Extracted Text Sample:</b> ${doc.extracted_text.substring(0, 200)}...</p>
            </div>`;
        });
        html += `</div>`;

        // Append general analysis sections to resultsContent - This will be updated below.

        // Risk Analysis - populate dedicated section (this section directly updates elements)
        const riskLevel = data.risk_analysis.risk_level.toLowerCase();
        scoreValue.className = `risk-score-display risk-${riskLevel}`;
        scoreValue.textContent = riskLevel.toUpperCase();

        // Risk Factors
        riskFactorsList.innerHTML = ''; // Clear previous list
        if (data.risk_analysis.risk_factors.length > 0) {
            data.risk_analysis.risk_factors.forEach(risk => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `
                    <b>Category:</b> ${risk.category} | 
                    <b>Severity:</b> <span class="risk-${risk.severity.toLowerCase()}">${risk.severity.toUpperCase()}</span><br>
                    <b>Pattern:</b> <code>${risk.pattern}</code><br>
                    <b>Context:</b> <pre>${risk.context}</pre>
                `;
                riskFactorsList.appendChild(listItem);
            });
        } else {
            const listItem = document.createElement('li');
            listItem.textContent = "No significant risk factors detected.";
            riskFactorsList.appendChild(listItem);
        }

        // Display the overall risk score and report if available from backend
        if (data.risk_score && data.report) {
            html += `<div class="card result-section"><h3>Vendor Credibility Score</h3>
                <p><b>Score:</b> ${data.risk_score.score}</p>
                <p><b>Risk Level:</b> <span class="risk-${data.risk_score.risk_level.toLowerCase()}">${data.risk_score.risk_level.toUpperCase()}</span></p>
            </div>`;
            html += `<div class="card result-section"><h3>Generated Report</h3>
                <p><b>Report Summary:</b></p><pre>${data.report.summary}</pre>
                <!-- Add more report details here as needed -->
            </div>`;
        }

        // Finally, set the results content and show the risk score section
        resultsContent.innerHTML = html; 
        resultsDiv.classList.remove('hidden');
        riskScoreSection.classList.remove('hidden');
    }
}); 