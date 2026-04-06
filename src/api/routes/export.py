import csv
import io

from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

@router.get("/{campaign_id}/export/csv")
async def export_csv(campaign_id: str):
    """
    Exports a tabular dump of the top candidates and their discovered contacts.
    """
    # Simulate DB fetch
    mock_data = [
        {"Company": "Google", "Role": "Senior Engineer", "Match": "98%", "Contact Name": "John Doe", "Contact Role": "Hiring Manager"},
        {"Company": "Stripe", "Role": "Backend Engineer", "Match": "95%", "Contact Name": "Jane Smith", "Contact Role": "Recruiter"}
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["Company", "Role", "Match", "Contact Name", "Contact Role"])
    writer.writeheader()
    writer.writerows(mock_data)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=campaign_{campaign_id}.csv"}
    )

@router.get("/{campaign_id}/export/pdf")
async def export_pdf(campaign_id: str):
    """
    Simulates generating a PDF brief.
    """
    return Response(
        content=b"%PDF-1.4\n% Mock PDF Content",
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=campaign_{campaign_id}.pdf"}
    )
