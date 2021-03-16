import {useState} from 'react';
import ProductList from './ProductList';

const Home = () => {
    /*This is how you make something reactive*/
    const [products, setProducts] = useState([
        {model: 'Macbook', retailer: 'BestBuy.com', available: 'yes', id: 1},
        {model: 'Vizio TV', retailer: 'BestBuy.com', available: 'yes', id: 2},
        {model: 'RTX 3090', retailer: 'BestBuy.com', available: 'no', id: 3},
      ]);
    
    const handleDelete = (id) => {
        //This does not change original data, only returns a new array with filtered data
        const newProducts = products.filter(blog => blog.id !== id);
        //now set reactive component with new array values
        setProducts(newProducts);
    }

    const [dateTime, setDateTime] = useState(Date().toLocaleString());

    const handleClick = () =>{
        setDateTime(Date().toLocaleString());
    }

    return (  
        <div className="home">
            <ProductList products={products} handleDelete={handleDelete}/>
            <h2>Homepage</h2>
            <p>{ dateTime }</p>
            <button onClick={handleClick}>Click me</button>
        </div>
    );
}
 
export default Home;