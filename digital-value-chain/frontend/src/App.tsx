
import React, { useState, useEffect } from 'react';
import { listOffers } from './api';

const App = () => {
  const [offers, setOffers] = useState([]);

  useEffect(() => {
    const fetchOffers = async () => {
      const data = await listOffers();
      setOffers(data);
    };
    fetchOffers();
  }, []);

  return (
    <div>
      <h1>Available Offers</h1>
      {offers.map((offer) => (
        <div key={offer.sku}>
          <h2>{offer.name}</h2>
          <p>{offer.description}</p>
          <button>Buy Now</button>
        </div>
      ))}
    </div>
  );
};

export default App;
