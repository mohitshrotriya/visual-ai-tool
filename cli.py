import click
import os
from pathlib import Path
from core.compare import compare_images
from core.ai_analyzer import analyze_diff
from core.reporter import generate_report
from core.capture import (
    save_baseline, save_current,
    get_baseline_path, get_current_path,
    baseline_exists
)
from config import DIFF_THRESHOLD

@click.group()
def cli():
    """🔍 Visual AI Testing Tool"""
    pass

@cli.command()
@click.argument('test_name')
@click.argument('image_path')
def set_baseline(test_name, image_path):
    """Baseline image set karo"""
    with open(image_path, "rb") as f:
        save_baseline(test_name, f.read())
    click.echo(f"✅ Baseline set: {test_name}")

@cli.command()
@click.argument('test_name')
@click.argument('image_path')
def compare(test_name, image_path):
    """Current image ko baseline se compare karo"""
    if not baseline_exists(test_name):
        click.echo(f"❌ Baseline nahi mili: {test_name}")
        click.echo(f"💡 Pehle run karo: python cli.py set-baseline {test_name} <image>")
        return

    with open(image_path, "rb") as f:
        save_current(test_name, f.read())

    baseline_path = get_baseline_path(test_name)
    current_path = get_current_path(test_name)

    click.echo(f"🔍 Comparing: {test_name}...")
    result = compare_images(baseline_path, current_path)

    diff_pct = result["diff_percentage"]
    click.echo(f"📊 Diff: {diff_pct}%")

    # Diff image save karo
    diff_path = str(Path("baselines") / test_name / "diff.png")
    result["diff_image"].save(diff_path)

    if diff_pct < DIFF_THRESHOLD:
        click.echo(f"✅ PASSED - Diff threshold ke andar hai")
        return

    click.echo(f"🤖 AI Analysis chal rahi hai...")
    ai_result = analyze_diff(baseline_path, current_path, diff_pct)

    click.echo(f"\n{'='*50}")
    click.echo(f"🐛 Bug: {ai_result['is_bug']}")
    click.echo(f"⚠️  Severity: {ai_result['severity']}")
    click.echo(f"📝 Summary: {ai_result['summary']}")
    click.echo(f"💡 Recommendation: {ai_result['recommendation']}")
    click.echo(f"{'='*50}\n")

    # Report generate karo
    report_path = generate_report([{
        "test_name": test_name,
        "baseline_path": baseline_path,
        "current_path": current_path,
        "diff_path": diff_path,
        "diff_percentage": diff_pct,
        "ai_analysis": ai_result
    }])
    click.echo(f"📄 Report: {report_path}")

@cli.command()
def serve():
    """Web UI server start karo"""
    import uvicorn
    from app import app
    click.echo("🚀 Server start ho raha hai: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    cli()
