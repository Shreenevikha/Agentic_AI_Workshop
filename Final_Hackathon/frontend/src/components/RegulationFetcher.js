import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import { ExpandMore, Search, Sync } from '@mui/icons-material';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const RegulationFetcher = () => {
  const [domain, setDomain] = useState('');
  const [entityType, setEntityType] = useState('');
  const [regulations, setRegulations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [domains, setDomains] = useState([]);
  const [entityTypes, setEntityTypes] = useState([]);

  // Sample data for demo
  const sampleDomains = ['GST', 'TDS', 'VAT', 'Income Tax'];
  const sampleEntityTypes = ['Company', 'Individual', 'Partnership', 'LLP'];

  useEffect(() => {
    // Load available domains and entity types
    setDomains(sampleDomains);
    setEntityTypes(sampleEntityTypes);
  }, []);

  const fetchRegulations = async () => {
    if (!domain || !entityType) {
      setError('Please select both domain and entity type');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post(getApiUrl('/api/v1/regulations/fetch'), {
        domain,
        entity_type: entityType,
      });

      if (response.data.success) {
        setRegulations(response.data.regulations || []);
        setSuccess(`Successfully fetched ${response.data.count} regulations`);
      } else {
        setError(response.data.error || 'Failed to fetch regulations');
      }
    } catch (err) {
      console.error('Error fetching regulations:', err);
      setError(err.response?.data?.detail || 'Failed to fetch regulations');
    } finally {
      setLoading(false);
    }
  };

  const syncSampleRegulations = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    const sampleRegulations = [
      // GST - Detailed Regulations
      {
        title: 'GST Registration Requirements for Individuals',
        content: `Individuals must register for GST if their annual turnover exceeds Rs. 20 lakhs (Rs. 10 lakhs for special category states). The registration process requires:

1. **PAN (Permanent Account Number)**: Mandatory for all GST registrations
2. **Aadhaar Number**: Required for authentication and verification
3. **Business Details**: Complete address, contact information, and business description
4. **Bank Account Details**: Valid bank account with IFSC code
5. **Digital Signature**: Class 2 or Class 3 digital signature certificate
6. **Business Documents**: Proof of business ownership or rental agreement

**Registration Process:**
- Apply online through GST portal (www.gst.gov.in)
- Upload required documents in specified formats
- Pay registration fees (varies by state)
- Receive GSTIN within 3-7 working days
- Display GSTIN on all invoices and business documents

**Compliance Requirements:**
- File monthly/quarterly returns (GSTR-1, GSTR-3B)
- Maintain proper books of accounts
- Issue tax invoices for all supplies
- Pay GST liability within due dates

**Penalties for Non-Compliance:**
- Late filing: Rs. 200 per day (maximum Rs. 5,000)
- Non-registration: 100% of tax due or Rs. 10,000 (whichever is higher)
- Incorrect invoicing: Rs. 25,000 per invoice`,
        domain: 'GST',
        entity_type: 'Individual',
        source_url: 'https://www.gst.gov.in/',
        version: '1.0',
      },
      {
        title: 'Comprehensive GST Registration for Companies',
        content: `Companies must register for GST if their annual turnover exceeds Rs. 40 lakhs (Rs. 20 lakhs for special category states). The registration process is mandatory for all companies engaged in supply of goods or services.

**Registration Requirements:**
1. **Company PAN**: Mandatory for all business entities
2. **Certificate of Incorporation**: Proof of company registration
3. **Board Resolution**: Authorizing GST registration
4. **Director Details**: PAN, Aadhaar, and contact information of all directors
5. **Business Address**: Registered office and additional place of business
6. **Bank Account**: Company bank account with IFSC code
7. **Digital Signature**: Class 2 or Class 3 DSC of authorized signatory

**Registration Process:**
- Apply through GST portal with company details
- Upload all required documents in PDF format
- Pay registration fees (varies by state and company type)
- Verification by GST authorities
- GSTIN allocation within 7-15 working days

**Post-Registration Compliance:**
- **Monthly Returns**: GSTR-1 (outward supplies), GSTR-3B (summary)
- **Quarterly Returns**: For small taxpayers (turnover < Rs. 5 crores)
- **Annual Return**: GSTR-9 (comprehensive annual return)
- **Reconciliation**: GSTR-9C (audit report for turnover > Rs. 2 crores)

**Input Tax Credit (ITC) Rules:**
- Claim ITC only on business-related expenses
- Maintain proper documentation for all purchases
- Reconcile ITC with supplier returns
- Reverse ITC for non-business use

**E-invoicing Requirements:**
- Mandatory for companies with turnover > Rs. 10 crores
- Generate IRN (Invoice Reference Number) for all B2B invoices
- Integrate with GST portal for real-time reporting

**Compliance Calendar:**
- GSTR-1: 11th of next month
- GSTR-3B: 20th of next month
- GSTR-9: 31st December of next financial year

**Penalties and Interest:**
- Late filing: Rs. 200 per day (max Rs. 5,000)
- Late payment: 18% interest on tax due
- Non-registration: 100% of tax due or Rs. 10,000
- Incorrect ITC: 100% of ITC claimed or Rs. 10,000`,
        domain: 'GST',
        entity_type: 'Company',
        source_url: 'https://www.gst.gov.in/',
        version: '1.1',
      },
      {
        title: 'GST Registration for Partnership Firms',
        content: `Partnership firms must register for GST if their annual turnover exceeds Rs. 20 lakhs. The registration process requires specific partnership-related documents and compliance procedures.

**Registration Requirements:**
1. **Partnership Deed**: Registered partnership deed with all terms
2. **Partners' PAN**: PAN cards of all partners
3. **Partners' Aadhaar**: Aadhaar numbers for verification
4. **Business Address**: Registered office and business locations
5. **Bank Account**: Partnership bank account details
6. **Digital Signature**: DSC of authorized partner

**Registration Process:**
- Apply through GST portal with partnership details
- Upload partnership deed and partner documents
- Pay applicable registration fees
- Verification by GST authorities
- GSTIN allocation within 5-10 working days

**Compliance Requirements:**
- File monthly/quarterly returns as applicable
- Maintain partnership accounts separately
- Issue invoices in partnership name
- Pay GST liability within due dates

**Partnership-Specific Rules:**
- All partners are jointly and severally liable for GST compliance
- Changes in partnership require GST registration amendment
- Dissolution requires GST cancellation application`,
        domain: 'GST',
        entity_type: 'Partnership',
        source_url: 'https://www.gst.gov.in/',
        version: '1.0',
      },
      {
        title: 'GST Registration for Limited Liability Partnerships (LLPs)',
        content: `LLPs must register for GST if their annual turnover exceeds Rs. 20 lakhs. LLPs enjoy limited liability while maintaining partnership flexibility.

**Registration Requirements:**
1. **LLP Agreement**: Registered LLP agreement with MCA
2. **LLP Registration Certificate**: Proof of LLP registration
3. **Designated Partners' Details**: PAN, Aadhaar, and contact information
4. **Business Address**: Registered office and business locations
5. **Bank Account**: LLP bank account with IFSC code
6. **Digital Signature**: DSC of designated partner

**Registration Process:**
- Apply through GST portal with LLP details
- Upload LLP registration certificate and agreement
- Pay registration fees as applicable
- Verification and GSTIN allocation

**LLP-Specific Compliance:**
- Designated partners are responsible for compliance
- Changes in designated partners require amendment
- Annual compliance certificate required
- Separate accounts for LLP and partners

**Tax Benefits for LLPs:**
- Lower tax rates compared to companies
- Flexibility in profit sharing
- Limited liability protection
- Simplified compliance procedures`,
        domain: 'GST',
        entity_type: 'LLP',
        source_url: 'https://www.gst.gov.in/',
        version: '1.0',
      },
      {
        title: 'GST Registration for Trusts and Societies',
        content: `Trusts and societies engaged in commercial activities must register for GST if their annual turnover exceeds Rs. 20 lakhs. Special provisions apply for charitable and religious activities.

**Registration Requirements:**
1. **Trust Deed/Society Registration**: Proof of registration
2. **Trustees/Office Bearers**: PAN and contact details
3. **Business Activities**: Description of commercial activities
4. **Bank Account**: Trust/society bank account
5. **Digital Signature**: DSC of authorized person

**Commercial vs Charitable Activities:**
- **Commercial Activities**: GST registration mandatory
- **Charitable Activities**: Exempt from GST
- **Mixed Activities**: Registration required for commercial portion

**Compliance Requirements:**
- Maintain separate accounts for commercial activities
- File returns for commercial supplies only
- Issue invoices for commercial transactions
- Pay GST on commercial activities

**Exemptions for Charitable Activities:**
- Educational services
- Healthcare services
- Religious activities
- Charitable donations`,
        domain: 'GST',
        entity_type: 'Trust',
        source_url: 'https://www.gst.gov.in/',
        version: '1.0',
      },
      // TDS - Detailed Regulations
      {
        title: 'TDS Deduction Rules for Individuals',
        content: `Individuals must deduct TDS (Tax Deducted at Source) on various payments as per Income Tax Act, 1961. The rates and thresholds vary based on the type of payment and payee.

**TDS Rates for Individuals:**
1. **Professional Fees (Section 194J)**: 10% on payments exceeding Rs. 30,000 per year
2. **Contract Payments (Section 194C)**: 1% for individuals, 2% for companies
3. **Rent (Section 194I)**: 10% on rent exceeding Rs. 2.4 lakhs per year
4. **Commission (Section 194H)**: 5% on commission exceeding Rs. 15,000 per year
5. **Interest (Section 194A)**: 10% on interest exceeding Rs. 40,000 per year

**TDS Deduction Process:**
- Calculate TDS amount based on applicable rate
- Deduct TDS before making payment
- Issue TDS certificate (Form 16A) to payee
- Deposit TDS to government within due dates
- File TDS returns quarterly

**Due Dates for TDS Payment:**
- **April to June**: 7th July
- **July to September**: 7th October
- **October to December**: 7th January
- **January to March**: 7th April

**TDS Return Filing:**
- **Form 26Q**: For payments other than salary
- **Form 24Q**: For salary payments
- **Due Date**: 31st of next month after quarter end

**Penalties for Non-Compliance:**
- Late deduction: Interest at 1% per month
- Late payment: Interest at 1.5% per month
- Late filing: Rs. 200 per day (max Rs. 1,00,000)
- Non-deduction: 100% of TDS amount as penalty

**TDS Certificate:**
- Issue Form 16A within 15 days of due date
- Contains TDS details and certificate number
- Required for claiming TDS credit

**Exemptions and Lower Deduction:**
- Apply for lower TDS certificate if needed
- Submit Form 13 for lower deduction
- Exemptions available for certain payments`,
        domain: 'TDS',
        entity_type: 'Individual',
        source_url: 'https://incometaxindia.gov.in/',
        version: '1.0',
      },
      {
        title: 'Comprehensive TDS Compliance for Companies',
        content: `Companies must comply with extensive TDS provisions under the Income Tax Act. The compliance requirements are more stringent for companies compared to individuals.

**TDS Rates for Companies:**
1. **Salary (Section 192)**: As per income tax slabs
2. **Contract Payments (Section 194C)**: 1% for individuals, 2% for companies
3. **Professional Fees (Section 194J)**: 10% on payments exceeding Rs. 30,000
4. **Rent (Section 194I)**: 10% on rent exceeding Rs. 2.4 lakhs
5. **Commission (Section 194H)**: 5% on commission exceeding Rs. 15,000
6. **Interest (Section 194A)**: 10% on interest exceeding Rs. 5,000
7. **Dividend (Section 194)**: 10% on dividend payments
8. **Royalty (Section 194J)**: 10% on royalty payments

**TDS Compliance Process:**
1. **Identification**: Identify payments liable for TDS
2. **Calculation**: Calculate TDS amount correctly
3. **Deduction**: Deduct TDS before payment
4. **Deposit**: Pay TDS to government within due dates
5. **Reporting**: File TDS returns quarterly
6. **Certification**: Issue TDS certificates to payees

**Due Dates for Companies:**
- **TDS Payment**: 7th of next month
- **TDS Return**: 31st of next month after quarter
- **TDS Certificate**: 15th of next month after quarter

**TDS Return Forms:**
- **Form 24Q**: For salary TDS
- **Form 26Q**: For non-salary TDS
- **Form 27Q**: For payments to non-residents
- **Form 27EQ**: For TCS (Tax Collected at Source)

**Compliance Requirements:**
- Maintain TDS registers and accounts
- Reconcile TDS with books of accounts
- File correction statements if needed
- Respond to TDS notices promptly

**Audit Requirements:**
- Tax audit mandatory if turnover > Rs. 1 crore
- TDS audit if TDS amount > Rs. 50 lakhs
- Maintain proper documentation for audit

**Penalties and Interest:**
- Late deduction: 1% per month interest
- Late payment: 1.5% per month interest
- Late filing: Rs. 200 per day (max Rs. 1,00,000)
- Non-deduction: 100% of TDS amount
- Incorrect deduction: Rs. 10,000 per default

**TDS Certificate Management:**
- Issue Form 16A for non-salary TDS
- Issue Form 16 for salary TDS
- Maintain certificate register
- Provide certificates on demand

**Digital Compliance:**
- Use digital signature for returns
- Maintain digital records
- Use TRACES portal for compliance
- Enable e-filing for all returns`,
        domain: 'TDS',
        entity_type: 'Company',
        source_url: 'https://incometax.gov.in/',
        version: '1.0',
      },
      {
        title: 'TDS Compliance for Partnership Firms',
        content: `Partnership firms must deduct TDS on various payments as per Income Tax Act. All partners are jointly responsible for TDS compliance.

**TDS Requirements:**
- Deduct TDS on salary payments to employees
- Deduct TDS on professional fees and contract payments
- Deduct TDS on rent, commission, and interest payments
- File TDS returns in partnership name

**Compliance Process:**
- Identify payments liable for TDS
- Calculate and deduct TDS correctly
- Deposit TDS within due dates
- File quarterly TDS returns
- Issue TDS certificates to payees

**Partnership-Specific Rules:**
- TDS registration in partnership name
- All partners jointly liable for compliance
- Changes in partnership require TDS amendment
- Dissolution requires TDS cancellation

**Penalties:**
- Late deduction: 1% per month interest
- Late payment: 1.5% per month interest
- Late filing: Rs. 200 per day penalty
- Non-deduction: 100% of TDS amount`,
        domain: 'TDS',
        entity_type: 'Partnership',
        source_url: 'https://incometaxindia.gov.in/',
        version: '1.0',
      },
      {
        title: 'TDS Compliance for Limited Liability Partnerships',
        content: `LLPs must comply with TDS provisions similar to companies but with partnership flexibility. Designated partners are responsible for compliance.

**TDS Requirements:**
- Deduct TDS on salary, contract, and professional payments
- Deduct TDS on rent, commission, and interest
- File TDS returns in LLP name
- Maintain proper TDS records

**Compliance Process:**
- Register for TDS in LLP name
- Deduct TDS on applicable payments
- Deposit TDS within due dates
- File quarterly returns
- Issue TDS certificates

**LLP-Specific Rules:**
- Designated partners responsible for compliance
- Changes in designated partners require amendment
- Limited liability protection for partners
- Simplified compliance compared to companies

**Benefits:**
- Lower compliance burden than companies
- Flexibility in profit sharing
- Limited liability protection
- Tax efficiency`,
        domain: 'TDS',
        entity_type: 'LLP',
        source_url: 'https://incometaxindia.gov.in/',
        version: '1.0',
      },
      // VAT - Detailed Regulations
      {
        title: 'VAT Registration and Compliance for Individuals',
        content: `Individuals selling goods must register for VAT (Value Added Tax) if their annual turnover exceeds Rs. 10 lakhs. VAT is a state-level tax on sale of goods.

**Registration Requirements:**
1. **PAN Card**: Mandatory for VAT registration
2. **Business Address**: Complete business location details
3. **Bank Account**: Business bank account details
4. **Business Documents**: Proof of business ownership
5. **Security Deposit**: Varies by state and turnover

**Registration Process:**
- Apply through state VAT portal
- Submit required documents
- Pay registration fees and security deposit
- Receive VAT registration certificate
- Display VAT number on invoices

**VAT Rates:**
- **0%**: Essential commodities, agricultural products
- **1%**: Precious metals, bullion
- **5%**: Industrial inputs, capital goods
- **12.5%**: General goods
- **20%**: Luxury items, tobacco, alcohol

**Compliance Requirements:**
- File monthly/quarterly VAT returns
- Maintain purchase and sale registers
- Issue tax invoices with VAT details
- Pay VAT liability within due dates
- Maintain proper books of accounts

**Input Tax Credit:**
- Claim ITC on purchases for business use
- Maintain purchase invoices
- Reconcile ITC with supplier returns
- Reverse ITC for non-business use

**Penalties:**
- Late filing: Rs. 100 per day
- Late payment: 2% per month interest
- Non-registration: 100% of tax due
- Incorrect invoicing: Rs. 5,000 per invoice

**VAT vs GST:**
- VAT replaced by GST from July 1, 2017
- Some states still have VAT for specific items
- Transition provisions available
- GST registration covers VAT requirements`,
        domain: 'VAT',
        entity_type: 'Individual',
        source_url: 'https://www.cbic.gov.in/',
        version: '1.0',
      },
      {
        title: 'VAT Registration and Compliance for Companies',
        content: `Companies engaged in sale of goods must register for VAT if their annual turnover exceeds Rs. 20 lakhs. Companies have more stringent compliance requirements.

**Registration Requirements:**
1. **Company PAN**: Mandatory for registration
2. **Certificate of Incorporation**: Proof of company registration
3. **Board Resolution**: Authorizing VAT registration
4. **Business Address**: Registered office and branches
5. **Bank Account**: Company bank account
6. **Security Deposit**: Higher amount for companies

**Registration Process:**
- Apply through state VAT portal
- Submit company documents
- Pay registration fees and security
- Verification by VAT authorities
- Receive VAT registration certificate

**VAT Rates for Companies:**
- **0%**: Exports, essential goods
- **1%**: Precious metals, bullion
- **5%**: Industrial inputs, capital goods
- **12.5%**: General goods
- **20%**: Luxury items, tobacco, alcohol

**Compliance Requirements:**
- File monthly VAT returns
- Maintain detailed purchase and sale registers
- Issue proper tax invoices
- Pay VAT liability within due dates
- Maintain audited accounts

**Input Tax Credit Rules:**
- Claim ITC on business purchases
- Maintain proper documentation
- Reconcile with supplier returns
- Reverse ITC for non-business use
- Carry forward unused ITC

**Audit Requirements:**
- Tax audit mandatory if turnover > Rs. 1 crore
- Maintain audit trail
- Submit audit reports
- Respond to audit queries

**Penalties for Companies:**
- Late filing: Rs. 200 per day
- Late payment: 2% per month interest
- Non-registration: 100% of tax due
- Incorrect invoicing: Rs. 10,000 per invoice
- Audit non-compliance: Rs. 1,00,000

**Digital Compliance:**
- Use digital signature for returns
- Maintain digital records
- Use state VAT portals
- Enable e-filing for all returns

**VAT to GST Transition:**
- GST registration covers VAT requirements
- Transition provisions available
- Carry forward VAT credit to GST
- File final VAT returns`,
        domain: 'VAT',
        entity_type: 'Company',
        source_url: 'https://www.cbic.gov.in/',
        version: '1.0',
      },
      // Income Tax - Detailed Regulations
      {
        title: 'Income Tax Slabs and Compliance for Individuals',
        content: `Individuals are taxed as per the applicable income tax slabs under the Income Tax Act, 1961. The tax rates vary based on age and income level.

**Income Tax Slabs (FY 2024-25):**
1. **Up to Rs. 3,00,000**: Nil (Basic exemption limit)
2. **Rs. 3,00,001 to Rs. 6,00,000**: 5% (Rebate under section 87A available)
3. **Rs. 6,00,001 to Rs. 9,00,000**: 10%
4. **Rs. 9,00,001 to Rs. 12,00,000**: 15%
5. **Rs. 12,00,001 to Rs. 15,00,000**: 20%
6. **Above Rs. 15,00,000**: 30%

**Rebate under Section 87A:**
- Available for total income up to Rs. 5,00,000
- Maximum rebate: Rs. 12,500
- Effectively no tax for income up to Rs. 5,00,000

**Surcharge:**
- **10%**: Income between Rs. 50 lakhs to Rs. 1 crore
- **15%**: Income between Rs. 1 crore to Rs. 2 crores
- **25%**: Income between Rs. 2 crores to Rs. 5 crores
- **37%**: Income above Rs. 5 crores

**Health and Education Cess:**
- 4% on income tax and surcharge

**Deductions Available:**
1. **Section 80C**: Up to Rs. 1.5 lakhs (PPF, ELSS, NSC, etc.)
2. **Section 80D**: Health insurance premium up to Rs. 25,000
3. **Section 80G**: Donations to charitable institutions
4. **Section 80TTA**: Interest on savings account up to Rs. 10,000
5. **Section 80TTB**: Interest on deposits up to Rs. 50,000 (senior citizens)

**Filing Requirements:**
- **Due Date**: July 31st of assessment year
- **Forms**: ITR-1 to ITR-7 based on income type
- **E-filing**: Mandatory for income above Rs. 5 lakhs
- **Digital Signature**: Required for e-filing

**Advance Tax:**
- **Due Dates**: June 15, September 15, December 15, March 15
- **Threshold**: Tax liability > Rs. 10,000
- **Penalty**: 1% per month for non-payment

**Penalties:**
- Late filing: Rs. 5,000 (max Rs. 10,000)
- Concealment: 50% to 200% of tax evaded
- Non-filing: Rs. 10,000

**Tax Planning Tips:**
- Invest in tax-saving instruments
- Claim all eligible deductions
- File returns on time
- Maintain proper documentation`,
        domain: 'Income Tax',
        entity_type: 'Individual',
        source_url: 'https://incometaxindia.gov.in/',
        version: '1.0',
      },
      {
        title: 'Corporate Tax Rates and Compliance for Companies',
        content: `Companies are taxed under the Income Tax Act, 1961. The tax rates vary based on turnover, type of company, and income source.

**Corporate Tax Rates (FY 2024-25):**

**For Domestic Companies:**
1. **Turnover up to Rs. 400 crores**: 25%
2. **Turnover above Rs. 400 crores**: 30%
3. **New Manufacturing Companies**: 15% (subject to conditions)

**For Foreign Companies:**
- **Royalty/FTS**: 50%
- **Other Income**: 40%

**Surcharge:**
- **7%**: Income between Rs. 1 crore to Rs. 10 crores
- **12%**: Income above Rs. 10 crores

**Health and Education Cess:**
- 4% on income tax and surcharge

**Minimum Alternate Tax (MAT):**
- **Rate**: 15% of book profits
- **Applicability**: When normal tax is less than MAT
- **Carry Forward**: MAT credit for 15 years

**Alternative Minimum Tax (AMT):**
- **Rate**: 18.5% of adjusted total income
- **Applicability**: For non-corporate entities

**Tax Deductions Available:**
1. **Section 35**: Research and development expenses
2. **Section 80G**: Donations to charitable institutions
3. **Section 80JJAA**: Employment of new employees
4. **Section 80M**: Inter-corporate dividends
5. **Section 80P**: Cooperative societies

**Filing Requirements:**
- **Due Date**: October 31st of assessment year
- **Forms**: ITR-6 for companies
- **E-filing**: Mandatory for all companies
- **Digital Signature**: Required for filing

**Audit Requirements:**
- **Tax Audit**: Mandatory if turnover > Rs. 1 crore
- **Transfer Pricing**: If international transactions > Rs. 1 crore
- **Country-by-Country Reporting**: For MNCs with turnover > Rs. 5,500 crores

**Advance Tax:**
- **Due Dates**: June 15, September 15, December 15, March 15
- **Installments**: 15%, 45%, 75%, 100% of estimated tax
- **Penalty**: 1% per month for non-payment

**Transfer Pricing:**
- **Arm's Length Price**: Required for international transactions
- **Documentation**: Maintain transfer pricing documentation
- **Audit**: Transfer pricing audit if transactions > Rs. 1 crore
- **Penalties**: 100% to 300% of tax adjustment

**Compliance Calendar:**
- **Advance Tax**: Quarterly installments
- **TDS Returns**: Monthly/quarterly
- **Income Tax Return**: October 31st
- **Tax Audit Report**: September 30th

**Penalties and Interest:**
- Late filing: Rs. 5,000 to Rs. 10,000
- Late payment: 1% per month interest
- Concealment: 50% to 200% of tax evaded
- Non-filing: Rs. 10,000

**Digital Compliance:**
- E-filing mandatory for all companies
- Digital signature required
- Maintain digital records
- Use income tax portal for all filings`,
        domain: 'Income Tax',
        entity_type: 'Company',
        source_url: 'https://incometaxindia.gov.in/',
        version: '1.0',
      }
    ];

    try {
      const response = await axios.post(getApiUrl('/api/v1/regulations/sync'), {
        regulations: sampleRegulations,
      });

      if (response.data.success) {
        setSuccess(`Successfully synced ${response.data.synced_count} regulations`);
      } else {
        setError(response.data.error || 'Failed to sync regulations');
      }
    } catch (err) {
      console.error('Error syncing regulations:', err);
      setError(err.response?.data?.detail || 'Failed to sync regulations');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Regulation Fetcher
      </Typography>

      {/* Search Form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Fetch Regulations
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Domain</InputLabel>
                <Select
                  value={domain}
                  label="Domain"
                  onChange={(e) => setDomain(e.target.value)}
                >
                  {domains.map((d) => (
                    <MenuItem key={d} value={d}>
                      {d}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Entity Type</InputLabel>
                <Select
                  value={entityType}
                  label="Entity Type"
                  onChange={(e) => setEntityType(e.target.value)}
                >
                  {entityTypes.map((et) => (
                    <MenuItem key={et} value={et}>
                      {et}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Button
                variant="contained"
                startIcon={<Search />}
                onClick={fetchRegulations}
                disabled={loading || !domain || !entityType}
                fullWidth
              >
                {loading ? <CircularProgress size={20} /> : 'Fetch Regulations'}
              </Button>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Button
                variant="outlined"
                color="primary"
                onClick={syncSampleRegulations}
                disabled={loading}
                fullWidth
              >
                {loading ? <CircularProgress size={20} /> : 'Sync Sample Data'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Results */}
      {regulations.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Regulations Found ({regulations.length})
            </Typography>
            <Grid container spacing={2}>
              {regulations.map((regulation, index) => (
                <Grid item xs={12} key={index}>
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Box sx={{ width: '100%' }}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {regulation.title}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                          <Chip 
                            label={regulation.domain} 
                            color="primary" 
                            size="small" 
                          />
                          <Chip 
                            label={regulation.entity_type} 
                            color="secondary" 
                            size="small" 
                          />
                          <Chip 
                            label={`v${regulation.version}`} 
                            variant="outlined" 
                            size="small" 
                          />
                          {regulation.source && (
                            <Chip 
                              label={regulation.source} 
                              color={regulation.source === 'database' ? 'success' : 'info'}
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </Box>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Box>
                        <Typography 
                          variant="body2" 
                          component="div"
                          sx={{ 
                            whiteSpace: 'pre-line',
                            fontSize: '0.875rem',
                            lineHeight: 1.8,
                            '& strong': {
                              fontWeight: 600,
                              color: 'primary.main'
                            },
                            '& ul, & ol': {
                              pl: 2,
                              mb: 1
                            },
                            '& li': {
                              mb: 0.5
                            }
                          }}
                          dangerouslySetInnerHTML={{
                            __html: regulation.content
                              .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                              .replace(/\n- /g, '\n• ')
                              .replace(/\n(\d+\. )/g, '\n$1')
                          }}
                        />
                        {regulation.source_url && (
                          <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                            <Typography variant="caption" color="text.secondary">
                              Source: <a href={regulation.source_url} target="_blank" rel="noopener noreferrer">
                                {regulation.source_url}
                              </a>
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </AccordionDetails>
                  </Accordion>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!loading && regulations.length === 0 && !error && (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" align="center">
              Select a domain and entity type to fetch regulations
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default RegulationFetcher; 