const Header = () => {

    componentDidMount() {
        this.interval = setInterval(() => this.setState({ time: Date.now() }), 1000);
      }
      componentWillUnmount() {
        clearInterval(this.interval);
      }

    return (  
        <nav className="header">
            <h1>Product Checker</h1>
            <p>{Date().toLocaleString()}</p>
        </nav>
    );
}
 
export default Header;