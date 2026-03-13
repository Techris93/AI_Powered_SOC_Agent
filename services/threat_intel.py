"""Threat Intelligence Service - Integrates with multiple threat intel sources"""
import aiohttp
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class ThreatIntelService:
    """Main threat intelligence service integrating multiple sources"""

    def __init__(self):
        self.abuseipdb_key = os.getenv("ABUSEIPDB_API_KEY", "")
        self.virustotal_key = os.getenv("VIRUSTOTAL_API_KEY", "")
        self.alienvault_key = os.getenv("ALIENVAULT_OTX_API_KEY", "")

    async def check_ip(self, ip_address: str) -> Dict[str, Any]:
        """
        Check IP address reputation across multiple sources

        Args:
            ip_address: IPv4 or IPv6 address

        Returns:
            Dictionary with threat intelligence data
        """
        results = {
            "ip": ip_address,
            "sources": {},
            "threat_score": 0,  # 0-100 score
            "is_malicious": False,
            "categories": [],
            "summary": ""
        }

        # Check AbuseIPDB
        if self.abuseipdb_key:
            try:
                abuseipdb_data = await self._check_abuseipdb(ip_address)
                results["sources"]["abuseipdb"] = abuseipdb_data

                if abuseipdb_data.get("abuseConfidenceScore", 0) > 0:
                    results["threat_score"] = max(
                        results["threat_score"],
                        abuseipdb_data.get("abuseConfidenceScore", 0)
                    )
                    if abuseipdb_data.get("abuseConfidenceScore", 0) > 50:
                        results["is_malicious"] = True
            except Exception as e:
                results["sources"]["abuseipdb"] = {"error": str(e)}

        # Check VirusTotal (if API key provided)
        if self.virustotal_key:
            try:
                vt_data = await self._check_virustotal_ip(ip_address)
                results["sources"]["virustotal"] = vt_data

                if vt_data.get("malicious", 0) > 0:
                    results["is_malicious"] = True
                    results["threat_score"] = max(results["threat_score"], 75)
            except Exception as e:
                results["sources"]["virustotal"] = {"error": str(e)}

        # Generate summary
        results["summary"] = self._generate_summary(results)

        return results

    async def check_domain(self, domain: str) -> Dict[str, Any]:
        """
        Check domain reputation

        Args:
            domain: Domain name

        Returns:
            Dictionary with threat intelligence data
        """
        results = {
            "domain": domain,
            "sources": {},
            "threat_score": 0,
            "is_malicious": False,
            "categories": [],
            "summary": ""
        }

        # Check VirusTotal (if API key provided)
        if self.virustotal_key:
            try:
                vt_data = await self._check_virustotal_domain(domain)
                results["sources"]["virustotal"] = vt_data

                if vt_data.get("malicious", 0) > 0:
                    results["is_malicious"] = True
                    results["threat_score"] = 80
            except Exception as e:
                results["sources"]["virustotal"] = {"error": str(e)}

        results["summary"] = self._generate_summary(results)

        return results

    async def check_hash(self, file_hash: str) -> Dict[str, Any]:
        """
        Check file hash reputation

        Args:
            file_hash: MD5, SHA1, or SHA256 hash

        Returns:
            Dictionary with threat intelligence data
        """
        results = {
            "hash": file_hash,
            "sources": {},
            "threat_score": 0,
            "is_malicious": False,
            "categories": [],
            "summary": ""
        }

        # Check VirusTotal (if API key provided)
        if self.virustotal_key:
            try:
                vt_data = await self._check_virustotal_hash(file_hash)
                results["sources"]["virustotal"] = vt_data

                if vt_data.get("malicious", 0) > 0:
                    results["is_malicious"] = True
                    results["threat_score"] = 90
            except Exception as e:
                results["sources"]["virustotal"] = {"error": str(e)}

        results["summary"] = self._generate_summary(results)

        return results

    async def _check_abuseipdb(self, ip_address: str) -> Dict[str, Any]:
        """Query AbuseIPDB API"""
        url = "https://api.abuseipdb.com/api/v2/check"

        headers = {
            "Accept": "application/json",
            "Key": self.abuseipdb_key
        }

        params = {
            "ipAddress": ip_address,
            "maxAgeInDays": 90,
            "verbose": True
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {})
                else:
                    return {"error": f"HTTP {response.status}"}

    async def _check_virustotal_ip(self, ip_address: str) -> Dict[str, Any]:
        """Query VirusTotal IP API"""
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip_address}"

        headers = {
            "x-apikey": self.virustotal_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    attributes = data.get("data", {}).get("attributes", {})
                    last_analysis_stats = attributes.get("last_analysis_stats", {})

                    return {
                        "malicious": last_analysis_stats.get("malicious", 0),
                        "suspicious": last_analysis_stats.get("suspicious", 0),
                        "harmless": last_analysis_stats.get("harmless", 0),
                        "undetected": last_analysis_stats.get("undetected", 0),
                        "reputation": attributes.get("reputation", 0)
                    }
                else:
                    return {"error": f"HTTP {response.status}"}

    async def _check_virustotal_domain(self, domain: str) -> Dict[str, Any]:
        """Query VirusTotal Domain API"""
        url = f"https://www.virustotal.com/api/v3/domains/{domain}"

        headers = {
            "x-apikey": self.virustotal_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    attributes = data.get("data", {}).get("attributes", {})
                    last_analysis_stats = attributes.get("last_analysis_stats", {})

                    return {
                        "malicious": last_analysis_stats.get("malicious", 0),
                        "suspicious": last_analysis_stats.get("suspicious", 0),
                        "harmless": last_analysis_stats.get("harmless", 0),
                        "undetected": last_analysis_stats.get("undetected", 0),
                        "reputation": attributes.get("reputation", 0)
                    }
                else:
                    return {"error": f"HTTP {response.status}"}

    async def _check_virustotal_hash(self, file_hash: str) -> Dict[str, Any]:
        """Query VirusTotal File Hash API"""
        url = f"https://www.virustotal.com/api/v3/files/{file_hash}"

        headers = {
            "x-apikey": self.virustotal_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    attributes = data.get("data", {}).get("attributes", {})
                    last_analysis_stats = attributes.get("last_analysis_stats", {})

                    return {
                        "malicious": last_analysis_stats.get("malicious", 0),
                        "suspicious": last_analysis_stats.get("suspicious", 0),
                        "harmless": last_analysis_stats.get("harmless", 0),
                        "undetected": last_analysis_stats.get("undetected", 0),
                        "file_type": attributes.get("type_description", "Unknown"),
                        "file_size": attributes.get("size", 0)
                    }
                else:
                    return {"error": f"HTTP {response.status}"}

    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate human-readable summary"""
        if results["is_malicious"]:
            return f"THREAT DETECTED - Threat score: {results['threat_score']}/100. This indicator is flagged as malicious by threat intelligence sources."
        elif results["threat_score"] > 30:
            return f"SUSPICIOUS - Threat score: {results['threat_score']}/100. This indicator shows some suspicious activity."
        else:
            return f"CLEAN - Threat score: {results['threat_score']}/100. No significant threats detected."


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        service = ThreatIntelService()

        # Test IP check
        result = await service.check_ip("1.1.1.1")  # Cloudflare DNS
        print(f"IP Check Result: {result}")

    asyncio.run(main())
