import { Component } from "react";
import 'bootstrap/dist/css/bootstrap.min.css';
import axios from "axios";

import { CSVLink } from "react-csv";

import { ProgressBar } from "react-bootstrap";

const headers = [
  {label:'Keyword',key:'Keyword'},  
  {label:'TF(%)(Avg)',key:'TF'},
  {label:'Occurrences',key:'Occur'},
  {label:'Word Count(Avg)',key:'WC'},
  {label:'DF(%)',key:'DF'},  
]

class App extends Component {
  constructor(props){
    super(props)
    this.state = {
      query:'',
      host: '',      
      message:'',
      processingBar:false,
      processingMax:1800,
      processingNow:0,
      urls:0,
      table:false,
      allgrams:[],
      trigrams_topics:[],
      data:[],
      download:false
    }
    this.alert = this.alert.bind(this)
    this.getKeywordsPercentage = this.getKeywordsPercentage.bind(this);
  }
  alert(e){
    setTimeout(()=>window.alert(e),500);
  }    
  componentDidMount(){
    document.title = 'SW Icresia';
  }
  async getKeywordsPercentage(){
    const s = this.state;

    if(s.query===''||s.host==='Country'||s.host==='') {
      this.alert('fill in both inputs');
      return
    }    

    this.setState({processingBar:true});            

    const interval = setInterval(()=>{
        this.setState({processingNow:this.state.processingNow+1})
    },1000)

    const results = await axios.get('http://13.37.227.4/words/'+s.query+'_'+s.host);    

    console.log(results.data.allgrams.length);

    clearInterval(interval);    

    this.setState({
      processingBar:false,
      data:results.data.allgrams,
      download:true,   
      totalResults:results.data.allgrams.length,
      processingNow:0,
      table:true,
      allgrams:results.data.allgrams
    })    
    
  }
  render(){
    return (
      <>
        <div className="m-4">
          <h1>SW Demo</h1>
          <p className="mt-4">Fill in the query and select host to get results</p>
          <div className="d-flex w-75">
            <input id='query' placeholder="Query" className="form-control" value={this.query} onChange={(e)=>this.setState({query:e.target.value})}/>
            <select id="host" className="form-control" value={this.host} onChange={e=>this.setState({host:e.target.value})}>
              <option>Country</option>
              <option>google.it</option>              
            </select>
            <button
              className="btn btn-primary rounded-0"
              onClick={this.getKeywordsPercentage}
            >Get</button>
            {
              this.state.download &&
              <CSVLink 
                data={this.state.data} 
                headers={headers}
                filename={this.state.query+'.csv'}     
                target='_blank'
                className="btn btn-success rounded-0"
                style={{width:230}}
              >Export CSV</CSVLink>
            }
          </div>          
          {
            this.state.processingBar &&
            <>
              <p className='mt-4'>Please wait</p>
              <ProgressBar now={this.state.processingNow} max={this.state.processingMax}/>
            </>
          }                    
          {
            this.state.table &&
            <div style={{display:'flex'}}>
              <div style={{marginTop:50}}>        
                <table style={{textAlign:'center',border:'1px solid black'}}>
                  <thead>
                    <tr>        
                      <th>Keyword</th>                                        
                      <th>TF(%)(Avg)</th>
                      <th>Occurrences</th>
                      <th>WC(Avg)</th>
                      <th>DF(%)</th>                    
                    </tr>
                  </thead>
                  <tbody>                  
                    {
                      this.state.allgrams.map(t=>{
                        return(
                          <tr>                          
                            <td style={{width:270,wordWrap:'break-word',display:'inline-block'}}>{t.Keyword}</td>
                            <td style={{width:150}}>{t.TF}</td>
                            <td style={{width:150}}>{t.Occur}</td>
                            <td style={{width:150}}>{t.WC}</td>
                            <td style={{width:150}}>{t.DF}</td>                             
                          </tr>
                        )      
                      })
                    }
                  </tbody>
                </table>
              </div>
              {/* <div style={{marginTop:50}}>        
                <table style={{textAlign:'center',border:'1px solid black'}}>
                  <thead>
                    <tr>        
                      <th>Keyword</th>                                        
                      <th>TF(%)(Avg)</th>
                      <th>Occurrences</th>
                      <th>WC(Avg)</th>
                      <th>DF(%)</th>                    
                    </tr>
                  </thead>
                  <tbody>                  
                    {
                      this.state.trigrams_topics.map(t=>{
                        return(
                          <tr>                          
                            <td style={{width:270,wordWrap:'break-word',display:'inline-block'}}>{t.Keyword}</td>
                            <td style={{width:150}}>{t.TF}</td>
                            <td style={{width:150}}>{t.Occur}</td>
                            <td style={{width:150}}>{t.WC}</td>
                            <td style={{width:150}}>{t.DF}</td>                             
                          </tr>
                        )      
                      })
                    }
                  </tbody>
                </table> 
              </div>*/}
            </div>
          }
        </div>
      </>
    );
  }
}

export default App;
