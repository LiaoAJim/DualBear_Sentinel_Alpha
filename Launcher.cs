using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace DualBear_Sentinel_Launcher
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            string appDir = AppDomain.CurrentDomain.BaseDirectory;
            string scriptPath = Path.Combine(appDir, "desktop_dashboard.py");
            
            if (!File.Exists(scriptPath))
            {
                MessageBox.Show("找不到啟動腳本: " + scriptPath, "錯誤", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            try
            {
                ProcessStartInfo psi = new ProcessStartInfo();
                // 使用 pythonw.exe 以避免彈出黑色終端機
                psi.FileName = "pythonw.exe";
                psi.Arguments = string.Format("\"{0}\"", scriptPath);
                psi.WorkingDirectory = appDir;
                psi.WindowStyle = ProcessWindowStyle.Hidden;
                psi.CreateNoWindow = true;
                psi.UseShellExecute = false;

                Process.Start(psi);
            }
            catch (Exception ex)
            {
                MessageBox.Show("啟動服務失敗: " + ex.Message, "系統錯誤", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}
