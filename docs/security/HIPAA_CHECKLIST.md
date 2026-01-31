# HIPAA Compliance Checklist for NeurAxis

## Administrative Safeguards

- [ ] **Risk Analysis (required)**: Conduct an accurate and thorough assessment of the potential risks and vulnerabilities to the confidentiality, integrity, and availability of ePHI.
- [ ] **Risk Management (required)**: Implement security measures sufficient to reduce risks and vulnerabilities to a reasonable and appropriate level.
- [ ] **Sanction Policy (required)**: Apply appropriate sanctions against workforce members who fail to comply with security policies and procedures.
- [ ] **Information System Activity Review (required)**: Implement procedures to regularly review records of information system activity (audit logs, access reports, and security incident tracking reports).

## Physical Safeguards

- [ ] **Workstation Use (required)**: Implement policies and procedures that specify the proper functions to be performed, the manner in which those functions are to be performed, and the physical attributes of the surroundings of a specific workstation.
- [ ] **Device and Media Controls (required)**: Implement policies and procedures that govern the receipt and removal of hardware and electronic media that contain ePHI into and out of a facility.

## Technical Safeguards

- [x] **Access Control**: Implement technical policies and procedures for electronic information systems that maintain ePHI to allow access only to those persons or software programs that have been granted access rights.
  - [x] Unique User Identification (required)
  - [ ] Emergency Access Procedure (required)
  - [ ] Automatic Logoff (addressable) - _Implemented via Frontend 15m timeout_
  - [x] Encryption and Decryption (addressable) - _Utilizing AES-256 for DB fields_
- [x] **Audit Controls (required)**: Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use ePHI. - _Implemented app/core/audit.py_
- [x] **Integrity (addressable)**: Implement policies and procedures to protect ePHI from improper alteration or destruction.
- [x] **Person or Entity Authentication (required)**: Implement procedures to verify that a person or entity seeking access to ePHI is the one claimed. - _MFA/JWT implementation_
- [x] **Transmission Security (addressable)**: Implement technical security measures to guard against unauthorized access to ePHI that is being transmitted over an electronic communications network. - _In-flight: TLS 1.3/HTTPS Only_

## Organizational Requirements

- [ ] **Business Associate Contracts (required)**: A covered entity may permit a business associate to create, receive, maintain, or transmit ePHI on the covered entity’s behalf only if the covered entity obtains satisfactory assurances.
