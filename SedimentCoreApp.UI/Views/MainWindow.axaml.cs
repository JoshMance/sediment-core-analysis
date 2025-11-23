using Avalonia.Controls;
using SedimentCoreApp.UI.ViewModels;

namespace SedimentCoreApp.UI.Views;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        DataContext = new MainWindowViewModel();
    }
}
