import { Component, OnInit } from '@angular/core';
import { firestoreWords } from 'src/common/networking/firebase';

@Component({
  selector: 'app-plotter',
  templateUrl: './plotter.component.html',
  styleUrls: ['./plotter.component.css']
})
export class PlotterComponent implements OnInit { 

  single: any;
  
  cardColor: string = '#232837';


ngOnInit(): void {

  
  firestoreWords.limit(36).orderBy('value', 'desc').onSnapshot(snapshot => {
    
    this.single = snapshot.docs.map(doc => doc.data());

  });


  }

  

}

