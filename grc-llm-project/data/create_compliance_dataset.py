import json
import jsonlines

def create_compliance_dataset():
    """Create comprehensive compliance Q&A dataset for fine-tuning"""
    
    # SOC 2 Control Questions and Answers
    soc2_data = [
        {
            "instruction": "Which SOC 2 control covers password requirements?",
            "input": "",
            "output": "SOC 2 CC6.1 (Logical and Physical Access Controls) covers password requirements. Organizations must implement password complexity, minimum length, expiration policies, and multi-factor authentication where appropriate to restrict logical access to system resources."
        },
        {
            "instruction": "What does SOC 2 CC7.1 require for system operations?",
            "input": "",
            "output": "SOC 2 CC7.1 requires organizations to ensure system capacity meets current processing requirements and is monitored to enable implementation of additional capacity to meet forecasted processing requirements."
        },
        {
            "instruction": "How does SOC 2 address data backup requirements?",
            "input": "",
            "output": "SOC 2 CC5.1 requires organizations to implement controls over the selection and development of general controls over technology to support the achievement of objectives. This includes backup and recovery procedures for critical data and systems."
        },
        {
            "instruction": "What is required for SOC 2 CC6.3 access reviews?",
            "input": "",
            "output": "SOC 2 CC6.3 requires organizations to authorize, modify, or remove access to data, software, functions, and other protected information assets based on roles and responsibilities. Regular access reviews must be performed to ensure appropriateness of access rights."
        },
        {
            "instruction": "Does SOC 2 require encryption of data in transit?",
            "input": "",
            "output": "Yes, SOC 2 CC6.7 requires the transmission of data and other communications to be protected. This typically includes encryption of sensitive data during transmission using protocols like TLS/SSL."
        }
    ]
    
    # ISO 27001 Control Questions and Answers
    iso27001_data = [
        {
            "instruction": "What does ISO 27001 say about access reviews?",
            "input": "",
            "output": "ISO 27001 A.9.2.5 requires regular user access rights reviews to ensure appropriateness. Organizations must review access rights at planned intervals and when changes occur, removing or adjusting access that is no longer required."
        },
        {
            "instruction": "Which ISO 27001 control addresses password management?",
            "input": "",
            "output": "ISO 27001 A.9.4.3 covers password management systems. It requires interactive password systems to ensure quality passwords and protect passwords from unauthorized access during transmission and storage."
        },
        {
            "instruction": "What does ISO 27001 require for incident management?",
            "input": "",
            "output": "ISO 27001 A.16.1.1 requires organizations to establish incident management responsibilities and procedures. This includes reporting security events quickly to appropriate management channels and responding to security incidents in a timely manner."
        },
        {
            "instruction": "How does ISO 27001 address supplier access management?",
            "input": "",
            "output": "ISO 27001 A.15.1.1 requires organizations to establish and implement policies for managing information security risks associated with supplier access. Access rights must be defined, documented, and regularly reviewed."
        },
        {
            "instruction": "What backup requirements does ISO 27001 specify?",
            "input": "",
            "output": "ISO 27001 A.12.3.1 requires regular backup copies of information, software and system images. Backup procedures should be regularly tested, and restoration capability verified to ensure business continuity requirements can be met."
        }
    ]
    
    # HIPAA Questions and Answers
    hipaa_data = [
        {
            "instruction": "Do we need encryption at rest for HIPAA?",
            "input": "",
            "output": "While HIPAA does not explicitly mandate encryption, it requires appropriate technical safeguards for ePHI. The Security Rule states encryption is 'addressable,' meaning covered entities must implement it or document why an alternative measure is more appropriate. AES-256 encryption at rest is considered a standard implementation."
        },
        {
            "instruction": "What does HIPAA require for access controls?",
            "input": "",
            "output": "HIPAA Security Rule §164.312(a)(1) requires implementation of technical policies and procedures that allow only authorized persons to access ePHI. This includes unique user identification, emergency access procedures, automatic logoff, and encryption and decryption capabilities."
        },
        {
            "instruction": "How does HIPAA address audit logs?",
            "input": "",
            "output": "HIPAA Security Rule §164.312(b) requires implementation of hardware, software, and/or procedural mechanisms that record and examine access and other activity in information systems containing ePHI. Audit logs must be protected from alteration and regularly reviewed."
        },
        {
            "instruction": "What are HIPAA's requirements for data transmission?",
            "input": "",
            "output": "HIPAA Security Rule §164.312(e)(1) requires technical security measures to guard against unauthorized access to ePHI transmitted over electronic communications networks. End-to-end encryption is required when ePHI is transmitted over open networks like the internet."
        },
        {
            "instruction": "Does HIPAA require regular security risk assessments?",
            "input": "",
            "output": "Yes, HIPAA Security Rule §164.308(a)(1)(ii)(A) requires covered entities to conduct regular security evaluations. Organizations must perform periodic technical and non-technical evaluations to ensure security measures continue to be reasonable and appropriate."
        }
    ]
    
    # Cross-framework comparative questions
    comparative_data = [
        {
            "instruction": "How do SOC 2, ISO 27001, and HIPAA differ in encryption requirements?",
            "input": "",
            "output": "SOC 2 CC6.7 requires protection during transmission but doesn't specify encryption methods. ISO 27001 A.10.1.1 addresses cryptographic controls as needed. HIPAA makes encryption 'addressable' meaning required unless documented alternative exists. All three frameworks generally expect strong encryption for sensitive data."
        },
        {
            "instruction": "Which frameworks require multi-factor authentication?",
            "input": "",
            "output": "SOC 2 CC6.1 requires MFA for privileged access and remote access. ISO 27001 A.9.4.2 covers secure log-on procedures which may include MFA. HIPAA doesn't explicitly require MFA but considers it a reasonable safeguard under access control requirements. SOC 2 has the most explicit MFA requirements."
        }
    ]
    
    # Combine all datasets
    all_data = soc2_data + iso27001_data + hipaa_data + comparative_data
    
    # Save in different formats
    
    # 1. Save as JSONL for training
    with jsonlines.open('data/compliance_training.jsonl', 'w') as writer:
        for item in all_data:
            writer.write(item)
    
    # 2. Save as JSON for reference
    with open('data/compliance_training.json', 'w') as f:
        json.dump(all_data, f, indent=2)
    
    # 3. Create evaluation subset (20% of data)
    eval_size = len(all_data) // 5
    eval_data = all_data[:eval_size]
    train_data = all_data[eval_size:]
    
    with jsonlines.open('data/compliance_eval.jsonl', 'w') as writer:
        for item in eval_data:
            writer.write(item)
    
    with jsonlines.open('data/compliance_train.jsonl', 'w') as writer:
        for item in train_data:
            writer.write(item)
    
    print(f"Dataset created:")
    print(f"  Total samples: {len(all_data)}")
    print(f"  Training samples: {len(train_data)}")
    print(f"  Evaluation samples: {len(eval_data)}")
    print(f"  SOC 2 questions: {len(soc2_data)}")
    print(f"  ISO 27001 questions: {len(iso27001_data)}")
    print(f"  HIPAA questions: {len(hipaa_data)}")
    print(f"  Comparative questions: {len(comparative_data)}")
    
    return all_data

if __name__ == "__main__":
    create_compliance_dataset()
