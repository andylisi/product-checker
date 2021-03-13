import Navbar from './Navbar';
import Home from './Home';

function App() {
  const title = 'Welcome to the Product Checker';
  const link = "https://www.reddit.com"

  return (
    <div className="App">
      <Navbar />                      {/*same as <Navbar></Navbar>*/}
      <div className="content">
        <Home />
      </div>
    </div>
  );
}

{/*always export component function so it can be used in other files - index.js*/}
export default App;
