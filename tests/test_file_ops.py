import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from proxmcp.proxmox import ProxmoxFileOps
from proxmcp.models import CommandResult

@pytest.mark.asyncio
async def test_proxmox_file_put_missing_local():
    runner = MagicMock()
    ops = ProxmoxFileOps(runner=runner)
    
    result = await ops.put("100", "nonexistent.txt", "/tmp/remote.txt")
    assert result.ok is False
    assert "Local file not found" in result.stderr
    runner.run.assert_not_called()

@pytest.mark.asyncio
async def test_proxmox_file_put_success():
    runner = MagicMock()
    runner.run = AsyncMock(return_value=CommandResult(
        ok=True, code=0, stdout="", stderr="", duration_ms=10, vmid="100", cmd="qm guest exec ..."
    ))
    
    ops = ProxmoxFileOps(runner=runner)
    
    # Mock TemporaryFTPServer, tempfile.TemporaryDirectory, and shutil.copy2
    mock_ftp = MagicMock()
    mock_ftp.port = 21212
    mock_ftp.get_reachable_ip.return_value = "192.168.1.90"
    mock_ftp.__enter__.return_value = mock_ftp
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("shutil.copy2"), \
         patch("tempfile.TemporaryDirectory", return_value=MagicMock(__enter__=MagicMock(return_value="/tmp/fake"))), \
         patch("proxmcp.proxmox.TemporaryFTPServer", return_value=mock_ftp):
        
        result = await ops.put("100", "local.txt", "/tmp/remote.txt")
        assert result.ok is True
        runner.run.assert_called_once()
        call_args = runner.run.call_args[1]
        assert "qm guest exec 100 -- bash -c" in call_args["cmd"]
        assert "urllib.request.urlretrieve" in call_args["cmd"]
        assert "ftp://192.168.1.90:21212/local.txt" in call_args["cmd"]

@pytest.mark.asyncio
async def test_proxmox_file_get_success():
    runner = MagicMock()
    runner.run = AsyncMock(return_value=CommandResult(
        ok=True, code=0, stdout="", stderr="", duration_ms=10, vmid="100", cmd="qm guest exec ..."
    ))
    
    ops = ProxmoxFileOps(runner=runner)
    
    mock_ftp = MagicMock()
    mock_ftp.port = 21212
    mock_ftp.get_reachable_ip.return_value = "192.168.1.90"
    mock_ftp.__enter__.return_value = mock_ftp
    
    with patch("tempfile.TemporaryDirectory", return_value=MagicMock(__enter__=MagicMock(return_value="/tmp/fake"))), \
         patch("proxmcp.proxmox.TemporaryFTPServer", return_value=mock_ftp), \
         patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value="file content")))))), \
         patch("pathlib.Path.exists", return_value=True):
        
        result = await ops.get("100", "/tmp/remote.txt")
        
        assert result.ok is True
        assert result.stdout == "file content"
        runner.run.assert_called_once()
        call_args = runner.run.call_args[1]
        assert "qm guest exec 100 -- bash -c" in call_args["cmd"]
        assert "ftplib import FTP" in call_args["cmd"]
        assert "ftp.storbinary" in call_args["cmd"]
