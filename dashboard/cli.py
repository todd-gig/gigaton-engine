#!/usr/bin/env python3
"""
Dashboard CLI — Generate and display the pipeline dashboard.

Usage:
  python -m dashboard              # Generate and open dashboard.html
  python -m dashboard --output PATH  # Save to custom path
"""
import sys
import os
import argparse
import webbrowser
from pathlib import Path

# Ensure project root is on path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dashboard.data_generator import generate_dashboard_data
from dashboard.html_renderer import render_html_dashboard


def main():
    """Generate dashboard and optionally open in browser."""
    parser = argparse.ArgumentParser(
        description="Gigaton Engine Pipeline Dashboard"
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output file path (default: dashboard.html in current directory)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Generate dashboard but don't open in browser",
    )

    args = parser.parse_args()

    # Determine output path
    output_path = args.output or "dashboard.html"
    output_path = Path(output_path).resolve()

    print(f"🔄 Generating dashboard data...")
    try:
        dashboard_data = generate_dashboard_data()
        print(f"   ✓ Processed {dashboard_data['summary']['total_prospects']} prospects")
        print(f"   ✓ Generated L1, L2, L3, L4, and segmentation data")
    except Exception as e:
        print(f"❌ Error generating dashboard data: {e}")
        sys.exit(1)

    print(f"🎨 Rendering HTML...")
    try:
        html_content = render_html_dashboard(dashboard_data)
        print(f"   ✓ Generated {len(html_content):,} bytes of HTML")
    except Exception as e:
        print(f"❌ Error rendering HTML: {e}")
        sys.exit(1)

    print(f"💾 Writing to {output_path}...")
    try:
        output_path.write_text(html_content, encoding="utf-8")
        print(f"   ✓ Dashboard saved")
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        sys.exit(1)

    # Open in browser if not suppressed
    if not args.no_open:
        print(f"🌐 Opening in browser...")
        try:
            webbrowser.open(f"file://{output_path}")
            print(f"   ✓ Browser opened")
        except Exception as e:
            print(f"⚠️  Could not open browser: {e}")

    print(f"\n✅ Dashboard ready: {output_path}")


if __name__ == "__main__":
    main()
