"""MCP Prompts — reusable workflow templates invoked by users."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nukemcp.server import NukeMCPServer


def register(server: NukeMCPServer):
    mcp = server.mcp

    @mcp.prompt()
    def greenscreen_comp(plate_path: str, bg_path: str) -> str:
        """Set up a full greenscreen composite from scratch.

        Creates a Read for the plate, a Read for the background, a keying pipeline
        (IBK or Keylight), despill, edge treatment, grade, merge, and Write node.

        Args:
            plate_path: Path to the greenscreen plate footage.
            bg_path: Path to the background plate footage.
        """
        return (
            f"Set up a complete greenscreen composite:\n\n"
            f"1. Create a Read node for the plate: {plate_path}\n"
            f"2. Create a Read node for the background: {bg_path}\n"
            f"3. Set up a keying pipeline on the plate using setup_keyer (IBKGizmo preferred)\n"
            f"4. Add despill using setup_despill\n"
            f"5. Set up edge treatment with setup_edge_blur\n"
            f"6. Add a Grade node for foreground color correction\n"
            f"7. Merge foreground over background using setup_basic_comp\n"
            f"8. Add a final Grade node for overall look\n"
            f"9. Create a Write node for output\n"
            f"10. Auto-layout the node graph\n\n"
            f"Use descriptive node names (fg_read, bg_read, fg_key, etc.)."
        )

    @mcp.prompt()
    def cg_integration(plate_path: str, cg_path: str) -> str:
        """Set up a CG element integration over a plate.

        Args:
            plate_path: Path to the background plate.
            cg_path: Path to the CG render (EXR with alpha).
        """
        return (
            f"Set up CG integration:\n\n"
            f"1. Create a Read node for the plate: {plate_path}\n"
            f"2. Create a Read node for the CG render: {cg_path}\n"
            f"3. Unpremult the CG if needed\n"
            f"4. Add a Grade node for CG color matching\n"
            f"5. Add a light wrap using setup_light_wrap\n"
            f"6. Premult the CG\n"
            f"7. Merge CG over plate using setup_basic_comp\n"
            f"8. Add a final Grade for the combined result\n"
            f"9. Create a Write node\n"
            f"10. Auto-layout\n\n"
            f"Use descriptive node names."
        )

    @mcp.prompt()
    def delivery_setup(
        source_node: str,
        output_path: str,
        file_format: str = "exr",
    ) -> str:
        """Configure delivery output with a Write node.

        Args:
            source_node: Name of the node to render from.
            output_path: Output file path.
            file_format: File format (exr, dpx, jpg, mov).
        """
        return (
            f"Set up delivery:\n\n"
            f"1. Connect a Write node to '{source_node}'\n"
            f"2. Set output path: {output_path}\n"
            f"3. Set format: {file_format}\n"
            f"4. If EXR: set compression to ZIP, channels to 'all'\n"
            f"5. If DPX: set bit depth to 10-bit\n"
            f"6. If MOV: set codec to ProRes 4444\n"
            f"7. Verify the colorspace matches the project settings"
        )

    @mcp.prompt()
    def cleanup_plate(plate_path: str) -> str:
        """Set up a plate cleanup workflow.

        Args:
            plate_path: Path to the plate footage.
        """
        return (
            f"Set up plate cleanup:\n\n"
            f"1. Create a Read node for: {plate_path}\n"
            f"2. Create a RotoPaint node for manual cleanup\n"
            f"3. Add a Denoise node if the plate is noisy\n"
            f"4. Add a Grade node for any exposure corrections\n"
            f"5. Create a Write node for output\n"
            f"6. Auto-layout"
        )
