#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "requests>=2.31.0",
#     "click>=8.1.0",
#     "rich>=13.0.0",
#     "lxml>=4.9.0",
# ]
# ///

"""
OAI-PMH Harvester for Riksarkivet
A self-contained script for harvesting metadata from the Swedish National Archives OAI-PMH repository.

Usage:
    uv run oai_pmh_harvester.py --help
    uv run oai_pmh_harvester.py identify
    uv run oai_pmh_harvester.py list-sets
    uv run oai_pmh_harvester.py list-identifiers SE_ULA
    uv run oai_pmh_harvester.py get-record "SE/ULA/10012/A I/2"
    uv run oai_pmh_harvester.py harvest --from-date 2024-01-01 --until-date 2024-12-31
    uv run oai_pmh_harvester.py recent SE_ULA --days 10 --limit 5
    uv run oai_pmh_harvester.py extract-pid "SE/ULA/10012/A I/2"
"""

# Legacy dont use

import sys
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

import click
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from lxml import etree

console = Console()

# Constants
OAI_BASE_URL = "https://oai-pmh.riksarkivet.se/OAI"
NAMESPACES = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ead": "urn:isbn:1-931666-22-9",
    "xlink": "http://www.w3.org/1999/xlink",
}


class OAIPMHClient:
    """Client for interacting with OAI-PMH repositories."""

    def __init__(self, base_url: str = OAI_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Riksarkivet OAI-PMH Harvester/1.0"})

    def _make_request(self, params: Dict[str, str], archive_set: Optional[str] = None) -> etree.Element:
        """Make an OAI-PMH request and return parsed XML."""
        # Build URL - archive sets are part of the URL path, not query parameters
        url = self.base_url
        if archive_set:
            url = f"{self.base_url}/{archive_set}"

        response = self.session.get(url, params=params)
        response.raise_for_status()

        # Parse XML
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(response.content, parser)

        # Check for OAI-PMH errors
        errors = root.xpath("//oai:error", namespaces=NAMESPACES)
        if errors:
            error_code = errors[0].get("code", "unknown")
            error_msg = errors[0].text or "Unknown error"
            raise Exception(f"OAI-PMH Error [{error_code}]: {error_msg}")

        return root

    def identify(self) -> Dict[str, str]:
        """Get repository identification information."""
        root = self._make_request({"verb": "Identify"})

        identify = root.xpath("//oai:Identify", namespaces=NAMESPACES)[0]

        return {
            "repository_name": self._get_text(identify, "oai:repositoryName") or "",
            "base_url": self._get_text(identify, "oai:baseURL") or "",
            "protocol_version": self._get_text(identify, "oai:protocolVersion") or "",
            "admin_email": self._get_text(identify, "oai:adminEmail") or "",
            "earliest_datestamp": self._get_text(identify, "oai:earliestDatestamp") or "",
            "deleted_record": self._get_text(identify, "oai:deletedRecord") or "",
            "granularity": self._get_text(identify, "oai:granularity") or "",
        }

    def list_sets(self) -> List[Dict[str, str]]:
        """List all available sets in the repository."""
        # This repository doesn't support ListSets, so return hardcoded list
        return [
            {
                "spec": "SE_RA",
                "name": "Riksarkivet (National Archives)",
                "description": "Medieval parchments, government records",
            },
            {
                "spec": "SE_KrA",
                "name": "Krigsarkivet (Military Archives)",
                "description": "Military records, war documentation",
            },
            {
                "spec": "SE_ULA",
                "name": "Uppsala landsarkiv",
                "description": "Church records, parish registers",
            },
            {
                "spec": "SE_GLA",
                "name": "Göteborg landsarkiv",
                "description": "Western Sweden regional archives",
            },
            {
                "spec": "SE_HLA",
                "name": "Härnösand landsarkiv",
                "description": "Northern Sweden regional archives",
            },
            {
                "spec": "SE_LLA",
                "name": "Lund landsarkiv",
                "description": "Southern Sweden regional archives",
            },
            {
                "spec": "SE_VALA",
                "name": "Vadstena landsarkiv",
                "description": "Central Sweden regional archives",
            },
            {
                "spec": "SE_ViLA",
                "name": "Visby landsarkiv",
                "description": "Gotland regional archives",
            },
            {
                "spec": "SE_ÖLA",
                "name": "Östersund landsarkiv",
                "description": "Northern inland regional archives",
            },
        ]

    def list_metadata_formats(self) -> List[Dict[str, str]]:
        """List supported metadata formats."""
        root = self._make_request({"verb": "ListMetadataFormats"})

        formats = []
        for format_elem in root.xpath("//oai:metadataFormat", namespaces=NAMESPACES):
            formats.append(
                {
                    "prefix": self._get_text(format_elem, "oai:metadataPrefix") or "",
                    "schema": self._get_text(format_elem, "oai:schema") or "",
                    "namespace": self._get_text(format_elem, "oai:metadataNamespace") or "",
                }
            )

        return formats

    def list_identifiers(
        self,
        set_spec: Optional[str] = None,
        metadata_prefix: str = "oai_ape_ead",
        from_date: Optional[str] = None,
        until_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List record identifiers, optionally filtered by set and date range."""
        params = {"verb": "ListIdentifiers", "metadataPrefix": metadata_prefix}

        # Don't include set in params - it's part of the URL
        if from_date:
            params["from"] = from_date
        if until_date:
            params["until"] = until_date

        root = self._make_request(params, archive_set=set_spec)

        identifiers = []
        for header in root.xpath("//oai:header", namespaces=NAMESPACES):
            # Skip deleted records
            if header.get("status") == "deleted":
                continue

            identifiers.append(
                {
                    "identifier": self._get_text(header, "oai:identifier") or "",
                    "datestamp": self._get_text(header, "oai:datestamp") or "",
                    "setSpec": self._get_text(header, "oai:setSpec") or "",
                }
            )

        # Check for resumption token (for pagination)
        resumption_token = root.xpath("//oai:resumptionToken", namespaces=NAMESPACES)
        if resumption_token and resumption_token[0].text:
            identifiers.append(
                {
                    "resumption_token": resumption_token[0].text,
                    "complete_list_size": resumption_token[0].get("completeListSize"),
                    "cursor": resumption_token[0].get("cursor"),
                }
            )

        return identifiers

    def get_record(self, identifier: str, metadata_prefix: str = "oai_ape_ead") -> Dict[str, Any]:
        """Get a specific record with full metadata."""
        params = {
            "verb": "GetRecord",
            "identifier": identifier,  # Don't pre-encode, requests will handle it
            "metadataPrefix": metadata_prefix,
        }

        root = self._make_request(params)

        record = root.xpath("//oai:record", namespaces=NAMESPACES)[0]
        header = record.xpath("oai:header", namespaces=NAMESPACES)[0]

        result = {
            "identifier": self._get_text(header, "oai:identifier") or "",
            "datestamp": self._get_text(header, "oai:datestamp") or "",
            "metadata_format": metadata_prefix,
        }

        # Extract metadata based on format
        if metadata_prefix == "oai_ape_ead":
            result.update(self._extract_ead_metadata(record))
        elif metadata_prefix == "oai_dc":
            result.update(self._extract_dc_metadata(record))

        return result

    def harvest_records(
        self,
        from_date: Optional[str] = None,
        until_date: Optional[str] = None,
        set_spec: Optional[str] = None,
        metadata_prefix: str = "oai_ape_ead",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Harvest multiple records within a date range."""
        # First get identifiers using ListIdentifiers
        identifiers = self.list_identifiers(set_spec, metadata_prefix, from_date, until_date)

        # Filter out resumption token info and only get actual records
        record_identifiers = [i for i in identifiers if "identifier" in i]

        # Apply limit if specified
        if limit:
            record_identifiers = record_identifiers[:limit]

        records = []
        total = len(record_identifiers)

        for idx, identifier_info in enumerate(record_identifiers):
            console.print(f"[cyan]Processing {idx + 1}/{total}: {identifier_info['identifier']}[/cyan]")
            try:
                # Get full record details for each identifier
                record = self.get_record(identifier_info["identifier"], metadata_prefix)
                records.append(record)
            except Exception as e:
                # Continue harvesting even if one record fails
                console.print(f"[yellow]Warning: Failed to get record {identifier_info['identifier']}: {e}[/yellow]")
                continue

        return records

    def get_recent_records(
        self,
        set_spec: str,
        days_back: int = 10,
        metadata_prefix: str = "oai_ape_ead",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get records modified within the last N days."""
        # Calculate date range
        until_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        console.print(f"[blue]Searching for records modified between {from_date} and {until_date} ({days_back} days back)[/blue]")

        return self.harvest_records(
            from_date=from_date,
            until_date=until_date,
            set_spec=set_spec,
            metadata_prefix=metadata_prefix,
            limit=limit,
        )

    def extract_pid(self, identifier: str) -> Optional[str]:
        """Extract PID from a record for IIIF access."""
        try:
            record = self.get_record(identifier, "oai_ape_ead")

            # Try to find NAD link
            if "nad_link" in record:
                # Extract PID from NAD link (last part after /)
                pid = record["nad_link"].split("/")[-1]
                return pid

            return None
        except Exception as e:
            console.print(f"[red]Error extracting PID: {e}[/red]")
            return None

    def _get_text(self, element, xpath: str) -> Optional[str]:
        """Safely extract text from an XML element."""
        result = element.xpath(xpath, namespaces=NAMESPACES)
        return result[0].text if result and result[0].text else None

    def _extract_ead_metadata(self, record) -> Dict[str, Any]:
        """Extract metadata from EAD format."""
        metadata = {}

        # Find EAD root
        ead = record.xpath(".//ead:ead", namespaces=NAMESPACES)
        if not ead:
            return metadata

        ead = ead[0]

        # Extract title
        title = ead.xpath(".//ead:unittitle", namespaces=NAMESPACES)
        if title and title[0].text:
            metadata["title"] = title[0].text

        # Extract date
        date = ead.xpath(".//ead:unitdate", namespaces=NAMESPACES)
        if date and date[0].text:
            metadata["date"] = date[0].text

        # Extract reference code
        ref_code = ead.xpath(".//ead:unitid", namespaces=NAMESPACES)
        if ref_code and ref_code[0].text:
            metadata["reference_code"] = ref_code[0].text

        # Extract scope content
        scope = ead.xpath(".//ead:scopecontent/ead:p", namespaces=NAMESPACES)
        if scope and scope[0].text:
            metadata["description"] = scope[0].text

        # Extract digital object links
        dao_image = ead.xpath('.//ead:dao[@xlink:role="IMAGE"]/@xlink:href', namespaces=NAMESPACES)
        if dao_image:
            metadata["image_viewer"] = dao_image[0]

        dao_manifest = ead.xpath('.//ead:dao[@xlink:role="MANIFEST"]/@xlink:href', namespaces=NAMESPACES)
        if dao_manifest:
            metadata["iiif_manifest"] = dao_manifest[0]

        # Extract NAD link
        nad_link = ead.xpath(".//ead:extref/@xlink:href", namespaces=NAMESPACES)
        if nad_link:
            for link in nad_link:
                if "sok.riksarkivet.se" in link or "sok-acc.riksarkivet.se" in link:
                    metadata["nad_link"] = link
                    break

        return metadata

    def _extract_dc_metadata(self, record) -> Dict[str, Any]:
        """Extract metadata from Dublin Core format."""
        metadata = {}

        # Extract DC fields
        dc_fields = {
            "title": "dc:title",
            "creator": "dc:creator",
            "subject": "dc:subject",
            "description": "dc:description",
            "date": "dc:date",
            "type": "dc:type",
            "format": "dc:format",
            "identifier": "dc:identifier",
            "source": "dc:source",
            "language": "dc:language",
            "relation": "dc:relation",
            "coverage": "dc:coverage",
            "rights": "dc:rights",
        }

        for field_name, xpath in dc_fields.items():
            values = record.xpath(f".//oai:metadata/{xpath}", namespaces=NAMESPACES)
            if values:
                # Get all values for multi-valued fields
                if len(values) > 1:
                    metadata[field_name] = [v.text for v in values if v.text]
                elif values[0].text:
                    metadata[field_name] = values[0].text

        return metadata


@click.group()
@click.pass_context
def cli(ctx):
    """OAI-PMH Harvester for Riksarkivet - Swedish National Archives."""
    ctx.obj = OAIPMHClient()


@cli.command()
@click.pass_obj
def identify(client):
    """Identify the OAI-PMH repository."""
    try:
        info = client.identify()

        # Create a nice table
        table = Table(title="Repository Information", show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        for key, value in info.items():
            if value:
                field_name = key.replace("_", " ").title()
                table.add_row(field_name, value)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command("list-sets")
@click.pass_obj
def list_sets(client):
    """List all available archive sets."""
    try:
        sets = client.list_sets()

        table = Table(title="Available Archive Sets")
        table.add_column("Set Code", style="cyan")
        table.add_column("Set Name", style="green")

        for s in sets:
            table.add_row(s["spec"], s["name"] or "")

        console.print(table)

        # Show common archive codes
        console.print("\n[yellow]Common Archive Codes:[/yellow]")
        console.print("SE_RA    - Riksarkivet (National Archives)")
        console.print("SE_KrA   - Krigsarkivet (Military Archives)")
        console.print("SE_ULA   - Uppsala landsarkiv")
        console.print("SE_GLA   - Göteborg landsarkiv")
        console.print("SE_HLA   - Härnösand landsarkiv")
        console.print("SE_LLA   - Lund landsarkiv")
        console.print("SE_VALA  - Vadstena landsarkiv")
        console.print("SE_ViLA  - Visby landsarkiv")
        console.print("SE_ÖLA   - Östersund landsarkiv")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command("list-identifiers")
@click.argument("set-spec", required=False)
@click.option("--metadata-prefix", default="oai_dc", help="Metadata format")
@click.option("--from-date", help="From date (YYYY-MM-DD)")
@click.option("--until-date", help="Until date (YYYY-MM-DD)")
@click.option("--limit", default=10, help="Number of records to display")
@click.pass_obj
def list_identifiers(client, set_spec, metadata_prefix, from_date, until_date, limit):
    """List record identifiers from a set or date range."""
    try:
        identifiers = client.list_identifiers(set_spec, metadata_prefix, from_date, until_date)

        # Filter out resumption token info
        records = [i for i in identifiers if "identifier" in i]
        resumption = [i for i in identifiers if "resumption_token" in i]

        # Create table
        table = Table(title="Record Identifiers" + (f" from {set_spec}" if set_spec else ""))
        table.add_column("Reference Code", style="cyan")
        table.add_column("Last Modified", style="green")

        for record in records[:limit]:
            table.add_row(record["identifier"], record["datestamp"])

        console.print(table)

        if len(records) > limit:
            console.print(f"\n[yellow]Showing {limit} of {len(records)} records[/yellow]")

        if resumption:
            r = resumption[0]
            if r.get("complete_list_size"):
                console.print(f"\n[yellow]Total records available: {r['complete_list_size']}[/yellow]")
            console.print("[yellow]Resumption token available for pagination[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command("get-record")
@click.argument("identifier")
@click.option("--metadata-prefix", default="oai_ape_ead", help="Metadata format")
@click.option("--output-format", type=click.Choice(["table", "json", "xml"]), default="table")
@click.pass_obj
def get_record(client, identifier, metadata_prefix, output_format):
    """Get detailed metadata for a specific record."""
    try:
        record = client.get_record(identifier, metadata_prefix)

        if output_format == "json":
            console.print_json(json.dumps(record, indent=2, ensure_ascii=False))
        elif output_format == "xml":
            # For XML, make raw request
            params = {
                "verb": "GetRecord",
                "identifier": identifier,
                "metadataPrefix": metadata_prefix,
            }
            response = requests.get(client.base_url, params=params)
            xml_str = response.text
            syntax = Syntax(xml_str, "xml", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            # Table format
            table = Table(title=f"Record: {identifier}")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            for key, value in record.items():
                if value:
                    field_name = key.replace("_", " ").title()
                    if isinstance(value, list):
                        value_str = ", ".join(str(v) for v in value)
                    else:
                        value_str = str(value)

                    # Truncate long values
                    if len(value_str) > 100:
                        value_str = value_str[:97] + "..."

                    table.add_row(field_name, value_str)

            console.print(table)

            # Special handling for IIIF links
            if "image_viewer" in record or "iiif_manifest" in record:
                console.print("\n[green]✓ Digital content available![/green]")
                if "image_viewer" in record:
                    console.print(f"Image viewer: {record['image_viewer']}")
                if "iiif_manifest" in record:
                    console.print(f"IIIF manifest: {record['iiif_manifest']}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--from-date", help="From date (YYYY-MM-DD)")
@click.option("--until-date", help="Until date (YYYY-MM-DD)")
@click.option("--set-spec", help="Limit to specific set")
@click.option("--metadata-prefix", default="oai_ape_ead", help="Metadata format")
@click.option("--output", type=click.Path(), help="Output file (JSON format)")
@click.option("--limit", default=5, help="Number of records to harvest")
@click.pass_obj
def harvest(client, from_date, until_date, set_spec, metadata_prefix, output, limit):
    """Harvest records within a date range."""
    try:
        records = client.harvest_records(from_date, until_date, set_spec, metadata_prefix, limit)

        console.print(f"[green]✓ Harvested {len(records)} records[/green]")

        if output:
            # Save to file
            output_path = Path(output)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            console.print(f"[green]✓ Saved to {output_path}[/green]")
        else:
            # Display summary
            table = Table(title="Harvested Records (first 10)")
            table.add_column("Identifier", style="cyan")
            table.add_column("Date", style="yellow")
            table.add_column("Title", style="green")

            for record in records[:10]:
                title = record.get("title", "N/A")
                if isinstance(title, list):
                    title = title[0] if title else "N/A"
                if len(title) > 50:
                    title = title[:47] + "..."

                date = record.get("date", "N/A")
                if isinstance(date, list):
                    date = date[0] if date else "N/A"

                table.add_row(record["identifier"], date, title)

            console.print(table)

            if len(records) > 10:
                console.print(f"\n[yellow]Showing 10 of {len(records)} records[/yellow]")
                console.print("[yellow]Use --output to save all records[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command("recent")
@click.argument("set-spec")
@click.option("--days", default=10, help="Number of days back to search")
@click.option("--limit", default=5, help="Maximum number of records to retrieve")
@click.option("--metadata-prefix", default="oai_ape_ead", help="Metadata format")
@click.option("--output", type=click.Path(), help="Output file (JSON format)")
@click.pass_obj
def recent(client, set_spec, days, limit, metadata_prefix, output):
    """Get records modified within the last N days."""
    try:
        records = client.get_recent_records(set_spec, days, metadata_prefix, limit)

        if not records:
            console.print(f"[yellow]No records found in {set_spec} modified within the last {days} days[/yellow]")
            return

        console.print(f"[green]✓ Found {len(records)} records modified in the last {days} days[/green]")

        if output:
            # Save to file
            output_path = Path(output)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            console.print(f"[green]✓ Saved to {output_path}[/green]")
        else:
            # Display summary
            table = Table(title=f"Recent Records (last {days} days)")
            table.add_column("Identifier", style="cyan")
            table.add_column("Modified", style="yellow")
            table.add_column("Title", style="green")

            for record in records:
                title = record.get("title", "N/A")
                if isinstance(title, list):
                    title = title[0] if title else "N/A"
                if len(title) > 50:
                    title = title[:47] + "..."

                modified_date = record.get("datestamp", "N/A")
                if modified_date != "N/A":
                    # Format the date nicely
                    try:
                        dt = datetime.fromisoformat(modified_date.replace("Z", "+00:00"))
                        modified_date = dt.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        pass  # Keep original format if parsing fails

                table.add_row(record["identifier"], modified_date, title)

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command("extract-pid")
@click.argument("identifier")
@click.pass_obj
def extract_pid(client, identifier):
    """Extract PID from a record for IIIF access."""
    try:
        pid = client.extract_pid(identifier)

        if pid:
            console.print(
                Panel(
                    f"[green bold]{pid}[/green bold]",
                    title="Extracted PID",
                    border_style="green",
                )
            )

            console.print("\n[yellow]How to use this PID:[/yellow]")
            console.print(f"1. IIIF Collection: https://lbiiif.riksarkivet.se/collection/arkiv/{pid}")
            console.print(f"2. With IIIF tools: ../iiif/step2_explore_collection.sh {pid}")
            console.print(f'3. MCP IIIF: mcp__oxenstierna__iiif_get_collection_info("{pid}")')

            # Also try to get the record to show if it has digital content
            record = client.get_record(identifier)
            if "image_viewer" in record or "iiif_manifest" in record:
                console.print("\n[green]✓ Digital content confirmed available![/green]")
        else:
            console.print("[red]Could not extract PID from this record[/red]")
            console.print("[yellow]The record may not have digital content available[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_obj
def demo(client):
    """Run a demonstration of all features."""
    console.print(
        Panel(
            "[bold cyan]OAI-PMH Harvester Demo[/bold cyan]\nThis will demonstrate all features of the harvester",
            border_style="cyan",
        )
    )

    # Step 1: Identify
    console.print("\n[bold]1. Repository Identification[/bold]")
    console.input("Press Enter to continue...")
    info = client.identify()
    console.print(f"Repository: {info['repository_name']}")
    console.print(f"Earliest record: {info['earliest_datestamp']}")

    # Step 2: List sets
    console.print("\n[bold]2. Available Archive Sets[/bold]")
    console.input("Press Enter to continue...")
    sets = client.list_sets()
    console.print(f"Found {len(sets)} archive sets")
    console.print(f"Example: {sets[0]['spec']} - {sets[0]['name']}")

    # Step 3: List identifiers
    console.print("\n[bold]3. List Records from Uppsala Archive[/bold]")
    console.input("Press Enter to continue...")
    identifiers = client.list_identifiers("SE_ULA")
    records = [i for i in identifiers if "identifier" in i]
    console.print(f"Found {len(records)} records")
    if records:
        console.print(f"Example: {records[0]['identifier']}")

    # Step 4: Get record
    console.print("\n[bold]4. Get Detailed Record[/bold]")
    console.input("Press Enter to continue...")
    test_id = "SE/ULA/10012/A I/2"
    record = client.get_record(test_id)
    console.print(f"Title: {record.get('title', 'N/A')}")
    console.print(f"Date: {record.get('date', 'N/A')}")

    # Step 5: Extract PID
    console.print("\n[bold]5. Extract PID for IIIF Access[/bold]")
    console.input("Press Enter to continue...")
    pid = client.extract_pid(test_id)
    if pid:
        console.print(f"[green]✓ PID: {pid}[/green]")

    console.print("\n[green bold]Demo complete![/green bold]")
    console.print("Try the individual commands to explore further.")


if __name__ == "__main__":
    cli()
