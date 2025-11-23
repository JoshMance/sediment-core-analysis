using Avalonia.Controls;
using SedimentCoreApp.UI.ViewModels;

namespace SedimentCoreApp.UI.Views;

public partial class CoreImageView : UserControl
{
    public CoreImageView()
    {
        InitializeComponent();
        DataContext = new CoreImageViewModel();
    }
}
