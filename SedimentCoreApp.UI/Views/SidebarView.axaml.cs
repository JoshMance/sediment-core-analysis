using Avalonia.Controls;
using SedimentCoreApp.UI.ViewModels;

namespace SedimentCoreApp.UI.Views;

public partial class SidebarView : UserControl
{
    public SidebarView()
    {
        InitializeComponent();
        DataContext = new SidebarViewModel();
    }
}
